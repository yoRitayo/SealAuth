# Testes do AuditLogger (auditoria.py), sem banco: sessão do SQLAlchemy sem conexão
import hashlib
import ipaddress
from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import auditoria
import pytest
from cripto import assinar, indice_email, verificar_assinatura
from database import entidades
from database.database import SessaoLocal
from sqlalchemy import event
from sqlalchemy.orm import Session, make_transient_to_detached

AGORA = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)


# ------- AUXILIARES -------------
def _usuario(**campos) -> entidades.Usuario:
    valores = dict(
        id=uuid4(),
        nome_usuario="ana",
        email="ana@exemplo.com",
        senha="hash-argon2",
        papel="usuario",
        status="ativo",
        falhas_consecutivas=0,
        criado_em=AGORA,
    )
    valores.update(campos)
    return entidades.Usuario(**valores)


def _persistente(sessao: Session, obj):
    # Simula um objeto já carregado do banco: valores atuais viram o estado "commitado"
    make_transient_to_detached(obj)
    sessao.add(obj)
    return obj


def _bloqueio(**campos) -> entidades.BloqueioIP:
    valores = dict(id=1, faixa="203.0.113.0/24", criado_em=AGORA, expira_em=AGORA + timedelta(hours=1))
    valores.update(campos)
    return entidades.BloqueioIP(**valores)


def _cadeia(n: int) -> list[SimpleNamespace]:
    registros, anterior = [], auditoria.HASH_GENESE
    for i in range(1, n + 1):
        dados = dict(
            id=i,
            criado_em=AGORA + timedelta(seconds=i),
            id_usuario=uuid4(),
            evento="login_falha",
            ip="203.0.113.7",
            jsonb={"motivo": "senha_incorreta", "tentativa": i},
        )
        hash_atual = auditoria.calcular_hash(
            anterior, dados["criado_em"], dados["id_usuario"], dados["evento"], dados["ip"], dados["jsonb"]
        )
        registros.append(
            SimpleNamespace(**dados, hash_anterior=anterior, hash_atual=hash_atual, assinatura=assinar(hash_atual.encode()))
        )
        anterior = hash_atual
    return registros


class _ResultadoFalso:
    def __init__(self, valor):
        self._valor = valor

    def scalar(self):
        return self._valor


class _ConexaoFalsa:
    # Responde ao advisory lock e à leitura do último hash, registrando as consultas
    def __init__(self, ultimo_hash=None):
        self.ultimo_hash = ultimo_hash
        self.chamadas = []

    def execute(self, instrucao, parametros=None):
        self.chamadas.append((str(instrucao), parametros))
        return _ResultadoFalso(None if "pg_advisory_xact_lock" in str(instrucao) else self.ultimo_hash)


def _sessao_com_conexao(conexao: _ConexaoFalsa) -> Session:
    sessao = Session()
    sessao.connection = lambda *args, **kwargs: conexao
    return sessao


def _logs_novos(sessao: Session) -> list[entidades.LogAuditoria]:
    return [o for o in sessao.new if isinstance(o, entidades.LogAuditoria)]


def _encadeados(logs: list[entidades.LogAuditoria]) -> list[entidades.LogAuditoria]:
    # Ordena pela própria cadeia (sessao.new não guarda ordem de inserção)
    por_anterior = {log.hash_anterior: log for log in logs}
    inicio = next(log for log in logs if log.hash_anterior not in {l.hash_atual for l in logs})
    ordenados = [inicio]
    while ordenados[-1].hash_atual in por_anterior:
        ordenados.append(por_anterior[ordenados[-1].hash_atual])
    return ordenados


@pytest.fixture
def ip_da_requisicao():
    def definir(valor):
        tokens.append(auditoria.ip_requisicao.set(valor))

    tokens = []
    yield definir
    for token in reversed(tokens):
        auditoria.ip_requisicao.reset(token)


# ------- SERIALIZAÇÃO -------------
def test_texto_ts_converte_para_utc():
    brasilia = datetime(2026, 10, 21, 9, 0, tzinfo=timezone(timedelta(hours=-3)))
    assert auditoria._texto_ts(brasilia) == "2026-10-21T12:00:00+00:00"


def test_texto_ts_preserva_microssegundos():
    assert auditoria._texto_ts(AGORA.replace(microsecond=123456)).endswith(".123456+00:00")


def test_texto_detalhes_e_canonico():
    assert auditoria._texto_detalhes({"b": 1, "a": 2}) == auditoria._texto_detalhes({"a": 2, "b": 1})
    assert auditoria._texto_detalhes({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_texto_detalhes_mantem_acentos():
    assert auditoria._texto_detalhes({"motivo": "não"}) == '{"motivo":"não"}'


# ------- CADEIA DE HASH -------------
def test_calcular_hash_segue_a_formula():
    id_usuario = uuid4()
    texto = "|".join(["0" * 64, AGORA.isoformat(), str(id_usuario), "login", "10.0.0.1", '{"a":1}'])
    esperado = hashlib.sha256(texto.encode()).hexdigest()
    assert auditoria.calcular_hash("0" * 64, AGORA, id_usuario, "login", "10.0.0.1", {"a": 1}) == esperado


def test_calcular_hash_usuario_nulo_vira_texto_vazio():
    texto = "|".join(["0" * 64, AGORA.isoformat(), "", "evento", "10.0.0.1", "{}"])
    esperado = hashlib.sha256(texto.encode()).hexdigest()
    assert auditoria.calcular_hash("0" * 64, AGORA, None, "evento", "10.0.0.1", {}) == esperado


def test_calcular_hash_independe_da_ordem_dos_detalhes():
    a = auditoria.calcular_hash("0" * 64, AGORA, None, "e", "1.1.1.1", {"x": 1, "y": 2})
    b = auditoria.calcular_hash("0" * 64, AGORA, None, "e", "1.1.1.1", {"y": 2, "x": 1})
    assert a == b


@pytest.mark.parametrize("campo", range(6))
def test_calcular_hash_muda_com_qualquer_campo(campo):
    base = ["0" * 64, AGORA, uuid4(), "login", "10.0.0.1", {"a": 1}]
    alterados = ["1" * 64, AGORA + timedelta(microseconds=1), uuid4(), "logout", "10.0.0.2", {"a": 2}]
    modificado = list(base)
    modificado[campo] = alterados[campo]
    assert auditoria.calcular_hash(*base) != auditoria.calcular_hash(*modificado)


# ------- VERIFICADOR -------------
def test_verificar_registros_vazio_e_integro():
    assert auditoria.verificar_registros([]) == {"integra": True, "total": 0, "quebra": None}


def test_verificar_registros_cadeia_integra():
    assert auditoria.verificar_registros(_cadeia(5)) == {"integra": True, "total": 5, "quebra": None}


def test_verificar_registros_detecta_dado_alterado():
    registros = _cadeia(5)
    registros[2].evento = "login_sucesso"
    resultado = auditoria.verificar_registros(registros)
    assert resultado == {"integra": False, "total": 3, "quebra": {"id": 3, "motivo": "hash_divergente"}}


def test_verificar_registros_detecta_ip_alterado():
    registros = _cadeia(3)
    registros[1].ip = "198.51.100.1"
    assert auditoria.verificar_registros(registros)["quebra"] == {"id": 2, "motivo": "hash_divergente"}


def test_verificar_registros_detecta_linha_apagada():
    registros = _cadeia(5)
    del registros[1]
    assert auditoria.verificar_registros(registros)["quebra"] == {"id": 3, "motivo": "encadeamento_quebrado"}


def test_verificar_registros_detecta_primeira_linha_sem_genese():
    registros = _cadeia(3)
    del registros[0]
    assert auditoria.verificar_registros(registros)["quebra"] == {"id": 2, "motivo": "encadeamento_quebrado"}


def test_verificar_registros_detecta_hash_recalculado_sem_chave():
    registros = _cadeia(3)
    r = registros[2]
    r.evento = "login_sucesso"
    r.hash_atual = auditoria.calcular_hash(r.hash_anterior, r.criado_em, r.id_usuario, r.evento, r.ip, r.jsonb)
    assert auditoria.verificar_registros(registros)["quebra"] == {"id": 3, "motivo": "assinatura_invalida"}


def test_verificar_registros_aceita_ids_nao_contiguos():
    registros = _cadeia(3)
    registros[1].id, registros[2].id = 10, 42  # rollback pode pular números da sequência
    assert auditoria.verificar_registros(registros)["integra"] is True


def test_verificar_registros_aceita_tipos_do_banco():
    # O banco devolve a assinatura como memoryview e o INET pode vir como objeto de IP
    registros = _cadeia(2)
    for r in registros:
        r.assinatura = memoryview(r.assinatura)
        r.ip = ipaddress.ip_address(r.ip)
    assert auditoria.verificar_registros(registros)["integra"] is True


def test_verificar_cadeia_le_o_log_em_ordem_de_id():
    registros = _cadeia(3)
    consultas = []

    class _DbFalso:
        def scalars(self, consulta):
            consultas.append(str(consulta))
            return iter(registros)

    assert auditoria.verificar_cadeia(_DbFalso()) == {"integra": True, "total": 3, "quebra": None}
    assert 'FROM "LOGS_AUDITORIA"' in consultas[0]
    assert 'ORDER BY "LOGS_AUDITORIA".id' in consultas[0]


# ------- DETECÇÃO DE MUDANÇAS -------------
def test_mudanca_em_objeto_novo():
    usuario = _usuario(status="pendente")
    assert auditoria._mudanca(usuario, "status") == (None, "pendente")


def test_mudanca_em_objeto_carregado():
    sessao = Session()
    usuario = _persistente(sessao, _usuario(status="ativo"))
    usuario.status = "bloqueado"
    assert auditoria._mudanca(usuario, "status") == ("ativo", "bloqueado")


def test_mudanca_sem_alteracao():
    sessao = Session()
    usuario = _persistente(sessao, _usuario(status="ativo"))
    assert auditoria._mudanca(usuario, "status") is None
    usuario.status = "ativo"  # mesmo valor
    assert auditoria._mudanca(usuario, "status") is None


@pytest.mark.parametrize(
    ("antes", "depois", "evento"),
    [
        ("ativo", "bloqueado", "conta_bloqueada"),
        ("pendente", "bloqueado", "conta_bloqueada"),
        ("pendente", "ativo", "conta_ativada"),
        ("bloqueado", "ativo", "conta_desbloqueada"),
        ("ativo", "pendente", "status_alterado"),
        (None, "ativo", "status_alterado"),
    ],
)
def test_evento_status(antes, depois, evento):
    assert auditoria._evento_status(antes, depois) == evento


def test_coletar_eventos_sessao_vazia():
    assert auditoria._coletar_eventos(Session()) == []


@pytest.mark.parametrize(("sucesso", "evento"), [(True, "login_sucesso"), (False, "login_falha")])
def test_coletar_eventos_tentativa_login(sucesso, evento):
    sessao, id_usuario = Session(), uuid4()
    sessao.add(
        entidades.TentativaLogin(
            id_usuario=id_usuario, nome_usuario_informado="ana", ip="10.0.0.1", com_sucesso=sucesso, motivo="m"
        )
    )
    assert auditoria._coletar_eventos(sessao) == [
        (id_usuario, evento, "10.0.0.1", {"motivo": "m", "username": "ana"})
    ]


def test_coletar_eventos_usuario_cadastrado_com_ator():
    sessao, ator = Session(), uuid4()
    sessao.info["ator_id"] = ator
    usuario = _usuario()
    sessao.add(usuario)
    assert auditoria._coletar_eventos(sessao) == [
        (usuario.id, "usuario_cadastrado", None, {"ator_id": str(ator), "papel": "usuario"})
    ]


def test_coletar_eventos_sem_ator_registra_nulo():
    sessao = Session()
    sessao.add(_usuario())
    assert auditoria._coletar_eventos(sessao)[0][3]["ator_id"] is None


def test_coletar_eventos_bloqueio_ip_e_alerta_novos():
    sessao, id_usuario = Session(), uuid4()
    sessao.add(_bloqueio())
    sessao.add(entidades.Alerta(id_usuario=id_usuario, evento="login_suspeito"))
    eventos = sorted(auditoria._coletar_eventos(sessao), key=lambda e: e[1])
    assert eventos == [
        (id_usuario, "alerta_criado", None, {"ator_id": None, "evento": "login_suspeito"}),
        (None, "ip_bloqueado", None, {"ator_id": None, "faixa": "203.0.113.0/24"}),
    ]


@pytest.mark.parametrize(
    ("campo", "antes", "depois", "evento", "extra"),
    [
        ("status", "ativo", "bloqueado", "conta_bloqueada", {"de": "ativo", "para": "bloqueado"}),
        ("status", "bloqueado", "ativo", "conta_desbloqueada", {"de": "bloqueado", "para": "ativo"}),
        ("status", "pendente", "ativo", "conta_ativada", {"de": "pendente", "para": "ativo"}),
        ("papel", "usuario", "analista", "papel_alterado", {"de": "usuario", "para": "analista"}),
        ("nome_usuario", "ana", "ana.silva", "nome_alterado", {"de": "ana", "para": "ana.silva"}),
        ("senha", "hash-velho", "hash-novo", "senha_alterada", {}),
    ],
)
def test_coletar_eventos_usuario_alterado(campo, antes, depois, evento, extra):
    sessao, ator = Session(), uuid4()
    sessao.info["ator_id"] = ator
    usuario = _persistente(sessao, _usuario(**{campo: antes}))
    setattr(usuario, campo, depois)
    assert auditoria._coletar_eventos(sessao) == [(usuario.id, evento, None, {"ator_id": str(ator), **extra})]


def test_coletar_eventos_varias_mudancas_no_mesmo_usuario():
    sessao = Session()
    usuario = _persistente(sessao, _usuario())
    usuario.papel = "admin"
    usuario.senha = "outro-hash"
    assert {e[1] for e in auditoria._coletar_eventos(sessao)} == {"papel_alterado", "senha_alterada"}


def test_coletar_eventos_ignora_so_contador_de_falhas():
    # A falha já é registrada pela tentativa de login
    sessao = Session()
    usuario = _persistente(sessao, _usuario())
    usuario.falhas_consecutivas = 3
    assert auditoria._coletar_eventos(sessao) == []


def test_coletar_eventos_bloqueio_ip_alterado():
    sessao = Session()
    bloqueio = _persistente(sessao, _bloqueio(id=7))
    bloqueio.expira_em = AGORA + timedelta(days=1)
    assert auditoria._coletar_eventos(sessao) == [
        (None, "bloqueio_ip_alterado", None, {"ator_id": None, "id_bloqueio": 7})
    ]


def test_coletar_eventos_usuario_excluido():
    sessao, ator = Session(), uuid4()
    sessao.info["ator_id"] = ator
    usuario = _persistente(sessao, _usuario())
    sessao.delete(usuario)
    assert auditoria._coletar_eventos(sessao) == [(usuario.id, "usuario_excluido", None, {"ator_id": str(ator)})]


# ------- GRAVAÇÃO NO before_flush -------------
def test_listener_registrado_no_before_flush():
    assert event.contains(SessaoLocal, "before_flush", auditoria._registrar_auditoria)


def test_registrar_auditoria_sem_eventos_nao_toca_no_banco():
    conexao = _ConexaoFalsa()
    sessao = _sessao_com_conexao(conexao)
    auditoria._registrar_auditoria(sessao, None, None)
    assert conexao.chamadas == []
    assert _logs_novos(sessao) == []


def test_registrar_auditoria_trava_antes_de_ler_o_ultimo_hash():
    conexao = _ConexaoFalsa()
    sessao = _sessao_com_conexao(conexao)
    sessao.add(_usuario())
    auditoria._registrar_auditoria(sessao, None, None)
    (lock, parametros), (leitura, _) = conexao.chamadas
    assert "pg_advisory_xact_lock" in lock and parametros == {"chave": auditoria.CHAVE_LOCK_LOG}
    assert "hash_atual" in leitura and "ORDER BY" in leitura and "DESC" in leitura


def test_registrar_auditoria_primeira_entrada_parte_da_genese():
    sessao = _sessao_com_conexao(_ConexaoFalsa(ultimo_hash=None))
    sessao.add(_usuario())
    auditoria._registrar_auditoria(sessao, None, None)
    (log,) = _logs_novos(sessao)
    assert log.hash_anterior == auditoria.HASH_GENESE
    assert log.evento == "usuario_cadastrado"


def test_registrar_auditoria_continua_do_ultimo_hash():
    sessao = _sessao_com_conexao(_ConexaoFalsa(ultimo_hash="a" * 64))
    sessao.add(_usuario())
    auditoria._registrar_auditoria(sessao, None, None)
    (log,) = _logs_novos(sessao)
    assert log.hash_anterior == "a" * 64


def test_registrar_auditoria_grava_entradas_encadeadas_e_assinadas():
    sessao = _sessao_com_conexao(_ConexaoFalsa())
    usuario = _usuario()
    sessao.add(usuario)
    sessao.add(
        entidades.TentativaLogin(
            id_usuario=usuario.id, nome_usuario_informado="ana", ip="10.0.0.1", com_sucesso=False, motivo="m"
        )
    )
    auditoria._registrar_auditoria(sessao, None, None)
    logs = _encadeados(_logs_novos(sessao))
    assert len(logs) == 2
    for i, log in enumerate(logs, start=1):
        log.id = i
        assert verificar_assinatura(log.hash_atual.encode(), log.assinatura)
        assert log.criado_em.tzinfo is not None
    assert logs[0].hash_anterior == auditoria.HASH_GENESE
    assert logs[1].hash_anterior == logs[0].hash_atual
    assert auditoria.verificar_registros(logs)["integra"] is True


def test_registrar_auditoria_usa_ip_da_tentativa(ip_da_requisicao):
    ip_da_requisicao("192.0.2.50")
    sessao = _sessao_com_conexao(_ConexaoFalsa())
    sessao.add(
        entidades.TentativaLogin(
            id_usuario=uuid4(), nome_usuario_informado="ana", ip="10.0.0.1", com_sucesso=True, motivo="sucesso"
        )
    )
    auditoria._registrar_auditoria(sessao, None, None)
    assert _logs_novos(sessao)[0].ip == "10.0.0.1"


def test_registrar_auditoria_usa_ip_da_requisicao(ip_da_requisicao):
    ip_da_requisicao("192.0.2.50")
    sessao = _sessao_com_conexao(_ConexaoFalsa())
    sessao.add(_usuario())
    auditoria._registrar_auditoria(sessao, None, None)
    assert _logs_novos(sessao)[0].ip == "192.0.2.50"


def test_registrar_auditoria_sem_ip_usa_padrao(ip_da_requisicao):
    ip_da_requisicao(None)
    sessao = _sessao_com_conexao(_ConexaoFalsa())
    sessao.add(_usuario())
    auditoria._registrar_auditoria(sessao, None, None)
    assert _logs_novos(sessao)[0].ip == "0.0.0.0"


# ------- ÍNDICE DO E-MAIL -------------
def test_listener_do_indice_registrado():
    assert event.contains(entidades.Usuario.email, "set", auditoria._atualizar_indice_email)


def test_indice_preenchido_ao_criar_usuario():
    assert _usuario(email="Ana@Exemplo.com").email_indice == indice_email("ana@exemplo.com")


def test_indice_acompanha_troca_de_email():
    usuario = _usuario(email="ana@exemplo.com")
    usuario.email = "bia@exemplo.com"
    assert usuario.email_indice == indice_email("bia@exemplo.com")


def test_indice_nulo_quando_email_nulo():
    usuario = _usuario()
    usuario.email = None
    assert usuario.email_indice is None
