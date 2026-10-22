# Testes do DetectionService (deteccao.py) e dos ganchos no login e no JWT, sem banco
import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import auditoria
import deteccao
import jwt
import pytest
import seguranca
from config import LIMITE_FALHAS_LOGIN
from controllers.auth_con import AuthController
from cripto import verificar_assinatura
from database import entidades
from fastapi import HTTPException
from schemas import Alerta, BloqueioIP, BloqueioIPCriar, TentativaLogin
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

IP = "203.0.113.7"


class _SessaoFalsa:
    # Responde às consultas na ordem dada e guarda o que foi adicionado
    def __init__(self, respostas=()):
        self.respostas = list(respostas)
        self.consultas, self.adicionados, self.commits, self.flushes = [], [], 0, 0

    def scalar(self, consulta):
        self.consultas.append(consulta)
        return self.respostas.pop(0) if self.respostas else None

    def add(self, obj):
        self.adicionados.append(obj)

    def flush(self):
        self.flushes += 1

    def commit(self):
        self.commits += 1


# Tipado como Any: a sessão falsa entra onde o código espera uma Session do SQLAlchemy
_DbFalso: Any = _SessaoFalsa


def _sql(consulta) -> str:
    return str(consulta.compile(dialect=postgresql.dialect()))


def _alertas(db) -> list[entidades.Alerta]:
    return [o for o in db.adicionados if isinstance(o, entidades.Alerta)]


def _bloqueios(db) -> list[entidades.BloqueioIP]:
    return [o for o in db.adicionados if isinstance(o, entidades.BloqueioIP)]


def _usuario(falhas: int) -> Any:
    return SimpleNamespace(id=uuid4(), falhas_consecutivas=falhas)


@pytest.fixture
def contagens(monkeypatch):
    # Substitui as contagens no banco: chave = motivo filtrado ou "distintos"
    valores = {"inexistentes": 0, "distintos": 0, "bloqueado": False}

    def contar(db, ip, *filtros, distintos=False):
        return valores["distintos"] if distintos else valores["inexistentes"]

    monkeypatch.setattr(deteccao, "_contar_tentativas", contar)
    monkeypatch.setattr(deteccao, "ip_bloqueado", lambda db, ip: valores["bloqueado"])
    return valores


# ------- FIREWALL -------------
@pytest.mark.parametrize("ip", ["testclient", "", "999.1.1.1"])
def test_ip_bloqueado_ignora_ip_invalido_sem_consultar(ip):
    db = _DbFalso()
    assert deteccao.ip_bloqueado(db, ip) is False
    assert db.consultas == []


def test_ip_bloqueado_consulta_faixa_cidr_e_expiracao():
    db = _DbFalso(respostas=[1])
    assert deteccao.ip_bloqueado(db, IP) is True
    sql = _sql(db.consultas[0])
    assert ">>= CAST" in sql and "AS INET" in sql
    assert "expira_em IS NULL" in sql and "expira_em >" in sql


def test_ip_bloqueado_sem_faixa_correspondente():
    assert deteccao.ip_bloqueado(_DbFalso(respostas=[None]), IP) is False


def test_firewall_responde_403_para_ip_bloqueado(monkeypatch):
    monkeypatch.setattr(deteccao, "ip_bloqueado", lambda db, ip: ip == IP)
    requisicao: Any = SimpleNamespace(client=SimpleNamespace(host=IP))
    with pytest.raises(HTTPException) as erro:
        deteccao.verificar_firewall(requisicao, _DbFalso())
    assert erro.value.status_code == 403


def test_firewall_libera_ip_nao_bloqueado(monkeypatch):
    monkeypatch.setattr(deteccao, "ip_bloqueado", lambda db, ip: False)
    requisicao: Any = SimpleNamespace(client=SimpleNamespace(host=IP))
    assert deteccao.verificar_firewall(requisicao, _DbFalso()) is None


# ------- ALERTAS E BLOQUEIOS -------------
def test_registrar_alerta_preenche_colunas_existentes():
    db, id_usuario = _DbFalso(), uuid4()
    alerta = deteccao.registrar_alerta(db, "forca_bruta", "alta", IP, "descrição", id_usuario, falhas=5)
    assert db.adicionados == [alerta]
    assert alerta.evento == "forca_bruta" and alerta.ip == IP and alerta.id_usuario == id_usuario
    assert alerta.jsonb == {"severidade": "alta", "descricao": "descrição", "falhas": 5}
    assert alerta.criado_em.tzinfo is not None


def test_registrar_alerta_e_assinado():
    alerta = deteccao.registrar_alerta(_DbFalso(), "enumeracao", "media", IP, "d")
    esperado = auditoria.calcular_hash("", alerta.criado_em, None, "enumeracao", IP, alerta.jsonb)
    assert alerta.hash_anterior == "" and alerta.hash_atual == esperado
    assert verificar_assinatura(alerta.hash_atual.encode(), alerta.assinatura)


@pytest.mark.parametrize(("ip", "faixa"), [(IP, "203.0.113.7/32"), ("2001:db8::1", "2001:db8::1/128")])
def test_bloquear_ip_por_30_minutos(ip, faixa):
    db = _DbFalso()
    alerta = deteccao.registrar_alerta(db, "credential_stuffing", "alta", ip, "d")
    bloqueio = deteccao.bloquear_ip(db, ip, alerta)
    assert bloqueio.faixa == faixa
    assert bloqueio.alerta is alerta
    assert bloqueio.expira_em is not None
    assert bloqueio.expira_em - bloqueio.criado_em == timedelta(minutes=deteccao.MINUTOS_BLOQUEIO_IP)


# ------- REGRAS DO IDS -------------
def test_analise_faz_flush_antes_de_contar(contagens):
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, None, deteccao.MOTIVO_USUARIO_INEXISTENTE)
    assert db.flushes == 1


def test_analise_ignora_ip_invalido(contagens):
    db = _DbFalso()
    deteccao.analisar_falha_login(db, "testclient", _usuario(5), "senha_incorreta")
    assert db.adicionados == [] and db.flushes == 0


@pytest.mark.parametrize(
    ("falhas", "regra", "severidade"),
    [(deteccao.FALHAS_CONTA_SUSPEITA, "conta_suspeita", "baixa"), (LIMITE_FALHAS_LOGIN, "forca_bruta", "alta")],
)
def test_regras_da_conta(contagens, falhas, regra, severidade):
    db, usuario = _DbFalso(), _usuario(falhas)
    deteccao.analisar_falha_login(db, IP, usuario, "senha_incorreta")
    (alerta,) = _alertas(db)
    assert (alerta.evento, alerta.jsonb["severidade"], alerta.id_usuario) == (regra, severidade, usuario.id)


@pytest.mark.parametrize("falhas", [1, 2, 4])
def test_sem_alerta_fora_dos_limiares_da_conta(contagens, falhas):
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, _usuario(falhas), "senha_incorreta")
    assert _alertas(db) == []


@pytest.mark.parametrize("motivo", ["conta_bloqueada", "conta_pendente_ativacao"])
def test_regras_da_conta_so_valem_para_senha_incorreta(contagens, motivo):
    # Conta já bloqueada continua com 5 falhas: não deve repetir o alerta de força bruta
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, _usuario(LIMITE_FALHAS_LOGIN), motivo)
    assert _alertas(db) == []


def test_enumeracao_alerta_ao_atingir_o_limiar(contagens):
    contagens["inexistentes"] = deteccao.LIMITE_USUARIOS_INEXISTENTES
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, None, deteccao.MOTIVO_USUARIO_INEXISTENTE)
    (alerta,) = _alertas(db)
    assert alerta.evento == "enumeracao" and alerta.id_usuario is None
    assert alerta.jsonb["tentativas"] == deteccao.LIMITE_USUARIOS_INEXISTENTES


@pytest.mark.parametrize("quantidade", [4, 6])
def test_enumeracao_nao_repete_alerta(contagens, quantidade):
    contagens["inexistentes"] = quantidade
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, None, deteccao.MOTIVO_USUARIO_INEXISTENTE)
    assert _alertas(db) == []


def test_enumeracao_so_conta_usuario_inexistente(contagens):
    contagens["inexistentes"] = deteccao.LIMITE_USUARIOS_INEXISTENTES
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, _usuario(1), "senha_incorreta")
    assert _alertas(db) == []


def test_credential_stuffing_alerta_e_bloqueia_ip(contagens):
    contagens["distintos"] = deteccao.LIMITE_USUARIOS_POR_IP
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, _usuario(1), "senha_incorreta")
    (alerta,) = _alertas(db)
    (bloqueio,) = _bloqueios(db)
    assert alerta.evento == "credential_stuffing" and alerta.jsonb["severidade"] == "alta"
    assert alerta.id_usuario is None and alerta.jsonb["usuarios"] == deteccao.LIMITE_USUARIOS_POR_IP
    assert bloqueio.alerta is alerta and bloqueio.faixa == f"{IP}/32"


def test_credential_stuffing_abaixo_do_limiar(contagens):
    contagens["distintos"] = deteccao.LIMITE_USUARIOS_POR_IP - 1
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, _usuario(1), "senha_incorreta")
    assert db.adicionados == []


def test_credential_stuffing_nao_bloqueia_ip_ja_bloqueado(contagens):
    contagens["distintos"], contagens["bloqueado"] = 15, True
    db = _DbFalso()
    deteccao.analisar_falha_login(db, IP, _usuario(1), "senha_incorreta")
    assert db.adicionados == []


def test_contar_tentativas_filtra_ip_e_janela():
    db = _DbFalso(respostas=[3])
    total = deteccao._contar_tentativas(db, IP, entidades.TentativaLogin.com_sucesso.is_(False), distintos=True)
    assert total == 3
    sql = _sql(db.consultas[0])
    assert 'count(DISTINCT "TENTATIVAS_LOGIN".nome_usuario_informado)' in sql
    assert '"TENTATIVAS_LOGIN".ip =' in sql and '"TENTATIVAS_LOGIN".atualizado_em >=' in sql
    assert "com_sucesso IS false" in sql


def test_contar_tentativas_sem_resultado_vira_zero():
    assert deteccao._contar_tentativas(_DbFalso(respostas=[None]), IP) == 0


def test_excesso_de_requisicoes_alerta_uma_vez_por_janela():
    db = _DbFalso(respostas=[0])
    deteccao.alertar_excesso_requisicoes(db, IP)
    (alerta,) = _alertas(db)
    assert alerta.evento == "excesso_requisicoes"
    parametros = db.consultas[0].compile(dialect=postgresql.dialect()).params
    assert "excesso_requisicoes" in parametros.values() and IP in parametros.values()

    repetido = _DbFalso(respostas=[1])
    deteccao.alertar_excesso_requisicoes(repetido, IP)
    assert repetido.adicionados == []


def test_token_invalido_usa_ip_da_requisicao_e_grava(monkeypatch):
    token = auditoria.ip_requisicao.set(IP)
    try:
        db = _DbFalso()
        deteccao.alertar_token_invalido(db, "InvalidSignatureError")
    finally:
        auditoria.ip_requisicao.reset(token)
    (alerta,) = _alertas(db)
    assert (alerta.evento, alerta.ip, alerta.jsonb["severidade"]) == ("token_invalido", IP, "alta")
    assert alerta.jsonb["motivo"] == "InvalidSignatureError"
    assert db.commits == 1


def test_token_invalido_sem_ip_valido_usa_padrao():
    token = auditoria.ip_requisicao.set("testclient")
    try:
        db = _DbFalso()
        deteccao.alertar_token_invalido(db, "x")
    finally:
        auditoria.ip_requisicao.reset(token)
    assert _alertas(db)[0].ip == "0.0.0.0"


# ------- GANCHO NO JWT (seguranca.py) -------------
def _usuario_ativo() -> entidades.Usuario:
    return entidades.Usuario(
        id=uuid4(), nome_usuario="ana", email="ana@exemplo.com", senha="h", papel="usuario",
        status="ativo", falhas_consecutivas=0, criado_em=datetime.now(UTC),
    )


def test_token_com_assinatura_invalida_gera_alerta(monkeypatch):
    chamadas = []
    monkeypatch.setattr(seguranca, "alertar_token_invalido", lambda db, motivo: chamadas.append(motivo))
    cabecalho, corpo, _ = seguranca.criar_token_acesso(uuid4()).split(".")
    with pytest.raises(HTTPException) as erro:
        seguranca.verificar_usuario(f"{cabecalho}.{corpo}.AAAA", _DbFalso())
    assert erro.value.status_code == 401
    assert chamadas == ["InvalidSignatureError"]


def test_token_com_algoritmo_trocado_gera_alerta(monkeypatch):
    chamadas = []
    monkeypatch.setattr(seguranca, "alertar_token_invalido", lambda db, motivo: chamadas.append(motivo))
    token = jwt.encode({"sub": str(uuid4()), "type": "access"}, "segredo-qualquer-com-32-bytes-ok", algorithm="HS256")
    with pytest.raises(HTTPException):
        seguranca.verificar_usuario(token, _DbFalso())
    assert chamadas == ["InvalidAlgorithmError"]


@pytest.mark.parametrize("motivo", ["malformado", "expirado"])
def test_token_malformado_ou_expirado_nao_gera_alerta(monkeypatch, motivo):
    chamadas = []
    monkeypatch.setattr(seguranca, "alertar_token_invalido", lambda db, m: chamadas.append(m))
    if motivo == "malformado":
        token = "nao.e.jwt"
    else:
        agora = datetime.now(UTC)
        token = jwt.encode(
            {"sub": str(uuid4()), "type": "access", "exp": agora - timedelta(minutes=1)},
            seguranca.CHAVE_PRIVADA, algorithm="RS256",
        )
    with pytest.raises(HTTPException):
        seguranca.verificar_usuario(token, _DbFalso())
    assert chamadas == []


# ------- GANCHO NO LOGIN (auth_con.py) -------------
def test_registrar_tentativa_aceita_usuario_inexistente():
    sessao = Session()
    AuthController._registrar_tentativa(
        sessao, None, "fantasma", IP, False, deteccao.MOTIVO_USUARIO_INEXISTENTE, datetime.now(UTC)
    )
    (tentativa,) = list(sessao.new)
    assert tentativa.id_usuario is None and tentativa.motivo == "usuario_inexistente"


class _LoginDb(_DbFalso):
    # Sessão falsa para o login: query(...).filter(...).first() devolve o usuário configurado
    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario

    def query(self, modelo):
        return self

    def filter(self, *args):
        return self

    def first(self):
        return self.usuario


def _login(monkeypatch, db, dentro_do_limite=True):
    monkeypatch.setattr("controllers.auth_con.verificar_rate_limit", lambda *a: dentro_do_limite)
    analises = []
    monkeypatch.setattr(
        "controllers.auth_con.analisar_falha_login", lambda db, ip, usuario, motivo: analises.append(motivo)
    )
    excessos = []
    monkeypatch.setattr("controllers.auth_con.alertar_excesso_requisicoes", lambda db, ip: excessos.append(ip))
    requisicao: Any = SimpleNamespace(client=SimpleNamespace(host=IP))
    formulario: Any = SimpleNamespace(username="fantasma", password="x")
    resposta: Any = SimpleNamespace()
    with pytest.raises(HTTPException) as erro:
        asyncio.run(AuthController().login(requisicao, resposta, formulario, db))
    return erro.value, analises, excessos


def test_login_de_usuario_inexistente_registra_e_analisa(monkeypatch):
    db = _LoginDb(usuario=None)
    erro, analises, _ = _login(monkeypatch, db)
    assert erro.status_code == 401 and erro.detail == "Usuário ou senha inválidos"
    (tentativa,) = db.adicionados
    assert tentativa.id_usuario is None and tentativa.motivo == "usuario_inexistente"
    assert analises == ["usuario_inexistente"] and db.commits == 1


def test_login_com_senha_errada_analisa(monkeypatch):
    usuario = _usuario_ativo()
    usuario.senha = seguranca.gerar_hash_senha("certa")
    db = _LoginDb(usuario=usuario)
    erro, analises, _ = _login(monkeypatch, db)
    assert erro.status_code == 401
    assert analises == ["senha_incorreta"] and usuario.falhas_consecutivas == 1


def test_login_acima_do_rate_limit_alerta_e_responde_429(monkeypatch):
    db = _LoginDb()
    erro, analises, excessos = _login(monkeypatch, db, dentro_do_limite=False)
    assert erro.status_code == 429
    assert excessos == [IP] and db.commits == 1 and analises == []


# ------- ESQUEMA -------------
def test_colunas_anulaveis_para_o_ids():
    assert entidades.Alerta.__table__.c.id_usuario.nullable is True
    assert entidades.TentativaLogin.__table__.c.id_usuario.nullable is True
    assert entidades.BloqueioIP.__table__.c.expira_em.nullable is True
    (chave,) = entidades.Alerta.__table__.c.id_usuario.foreign_keys
    assert chave.ondelete == "SET NULL"


def test_schemas_aceitam_nulos_do_ids():
    agora = datetime.now(UTC)
    assert Alerta(id=1, id_usuario=None, evento="enumeracao", ip=IP, jsonb={}, hash_anterior="",
                  hash_atual="h", assinatura=b"a", criado_em=agora).id_usuario is None
    assert TentativaLogin(id=1, id_usuario=None, nome_usuario_informado="x", ip=IP, com_sucesso=False,
                          motivo="usuario_inexistente", atualizado_em=agora).id_usuario is None
    assert BloqueioIP(id=1, id_alerta=None, faixa="203.0.113.0/24", criado_em=agora, expira_em=None).expira_em is None


def test_bloqueio_manual_aceita_expiracao():
    expira = datetime.now(UTC) + timedelta(hours=1)
    assert BloqueioIPCriar(faixa="203.0.113.0/24", expira_em=expira).expira_em == expira
    assert BloqueioIPCriar(faixa="203.0.113.0/24").expira_em is None
