# AuditLogger: log de auditoria em cadeia SHA-256, cada entrada assinada com RSA-PSS.
# Os eventos são detectados por um listener before_flush do SQLAlchemy, então o log é
# gravado na mesma transação da mudança que ele descreve, sem chamadas nos controllers.
import hashlib
import json
from collections.abc import Iterable
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from cripto import assinar, indice_email, verificar_assinatura
from database import entidades
from database.database import SessaoLocal
from sqlalchemy import event, inspect, select, text
from sqlalchemy.orm import Session

HASH_GENESE = "0" * 64
# Serializa as inserções no log: sem isso, duas transações leem o mesmo hash_anterior
CHAVE_LOCK_LOG = 424242

# IP da requisição atual, preenchido por um middleware em main.py
ip_requisicao: ContextVar[str | None] = ContextVar("ip_requisicao", default=None)


# ------- CADEIA DE HASH -------------
def _texto_ts(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat()


def _texto_detalhes(detalhes: dict[str, Any]) -> str:
    # JSONB não preserva a ordem das chaves: a serialização precisa ser canônica
    return json.dumps(detalhes, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def calcular_hash(
    hash_anterior: str,
    ts: datetime,
    id_usuario: Any,
    evento: str,
    ip: str,
    detalhes: dict[str, Any],
) -> str:
    # hash_atual = SHA-256(hash_anterior || ts || usuario_id || evento || ip || detalhes)
    partes = [
        hash_anterior,
        _texto_ts(ts),
        "" if id_usuario is None else str(id_usuario),
        evento,
        ip,
        _texto_detalhes(detalhes),
    ]
    return hashlib.sha256("|".join(partes).encode()).hexdigest()


def verificar_registros(registros: Iterable[Any]) -> dict[str, Any]:
    # Confere o encadeamento, o hash e a assinatura de cada entrada, na ordem de inserção.
    # Não exige ids contíguos: um rollback pode pular números da sequência.
    anterior = HASH_GENESE
    total = 0
    for registro in registros:
        total += 1
        motivo = None
        if registro.hash_anterior != anterior:
            motivo = "encadeamento_quebrado"
        elif registro.hash_atual != calcular_hash(
            registro.hash_anterior,
            registro.criado_em,
            registro.id_usuario,
            registro.evento,
            str(registro.ip),
            registro.jsonb,
        ):
            motivo = "hash_divergente"
        elif not verificar_assinatura(
            registro.hash_atual.encode(), bytes(registro.assinatura)
        ):
            motivo = "assinatura_invalida"
        if motivo:
            return {
                "integra": False,
                "total": total,
                "quebra": {"id": registro.id, "motivo": motivo},
            }
        anterior = registro.hash_atual
    return {"integra": True, "total": total, "quebra": None}


def verificar_cadeia(db: Session) -> dict[str, Any]:
    registros = db.scalars(
        select(entidades.LogAuditoria).order_by(entidades.LogAuditoria.id)
    )
    return verificar_registros(registros)


# ------- DETECÇÃO DOS EVENTOS -------------
def _mudanca(obj: Any, campo: str) -> tuple[Any, Any] | None:
    historico = inspect(obj).attrs[campo].history
    if not historico.has_changes():
        return None
    antes = historico.deleted[0] if historico.deleted else None
    depois = historico.added[0] if historico.added else None
    return None if antes == depois else (antes, depois)


def _evento_status(antes: str | None, depois: str | None) -> str:
    if depois == "bloqueado":
        return "conta_bloqueada"
    if antes == "pendente" and depois == "ativo":
        return "conta_ativada"
    if antes == "bloqueado" and depois == "ativo":
        return "conta_desbloqueada"
    return "status_alterado"


def _coletar_eventos(sessao: Session) -> list[tuple[Any, str, str | None, dict]]:
    # Cada evento: (id_usuario, evento, ip próprio ou None, detalhes)
    ator = sessao.info.get("ator_id")
    base = {"ator_id": None if ator is None else str(ator)}
    eventos = []

    for obj in sessao.new:
        if isinstance(obj, entidades.TentativaLogin):
            eventos.append(
                (
                    obj.id_usuario,
                    "login_sucesso" if obj.com_sucesso else "login_falha",
                    obj.ip,
                    {"motivo": obj.motivo, "username": obj.nome_usuario_informado},
                )
            )
        elif isinstance(obj, entidades.Usuario):
            eventos.append((obj.id, "usuario_cadastrado", None, {**base, "papel": obj.papel}))
        elif isinstance(obj, entidades.BloqueioIP):
            eventos.append((None, "ip_bloqueado", None, {**base, "faixa": str(obj.faixa)}))
        elif isinstance(obj, entidades.Alerta):
            eventos.append((obj.id_usuario, "alerta_criado", None, {**base, "evento": obj.evento}))

    for obj in sessao.dirty:
        if isinstance(obj, entidades.Usuario):
            if mudanca := _mudanca(obj, "status"):
                antes, depois = mudanca
                detalhes = {**base, "de": antes, "para": depois}
                eventos.append((obj.id, _evento_status(antes, depois), None, detalhes))
            if mudanca := _mudanca(obj, "papel"):
                antes, depois = mudanca
                eventos.append((obj.id, "papel_alterado", None, {**base, "de": antes, "para": depois}))
            if _mudanca(obj, "senha"):
                eventos.append((obj.id, "senha_alterada", None, base))
            if mudanca := _mudanca(obj, "nome_usuario"):
                antes, depois = mudanca
                eventos.append((obj.id, "nome_alterado", None, {**base, "de": antes, "para": depois}))
        elif isinstance(obj, entidades.BloqueioIP) and sessao.is_modified(obj):
            eventos.append((None, "bloqueio_ip_alterado", None, {**base, "id_bloqueio": obj.id}))

    for obj in sessao.deleted:
        if isinstance(obj, entidades.Usuario):
            eventos.append((obj.id, "usuario_excluido", None, base))

    return eventos


@event.listens_for(SessaoLocal, "before_flush")
def _registrar_auditoria(sessao: Session, contexto, instancias) -> None:
    eventos = _coletar_eventos(sessao)
    if not eventos:
        return

    conexao = sessao.connection()
    conexao.execute(text("SELECT pg_advisory_xact_lock(:chave)"), {"chave": CHAVE_LOCK_LOG})
    anterior = conexao.execute(
        select(entidades.LogAuditoria.hash_atual)
        .order_by(entidades.LogAuditoria.id.desc())
        .limit(1)
    ).scalar() or HASH_GENESE

    ip_padrao = ip_requisicao.get() or "0.0.0.0"
    for id_usuario, evento, ip, detalhes in eventos:
        ts = datetime.now(UTC)
        ip = str(ip or ip_padrao)
        hash_atual = calcular_hash(anterior, ts, id_usuario, evento, ip, detalhes)
        sessao.add(
            entidades.LogAuditoria(
                id_usuario=id_usuario,
                evento=evento,
                ip=ip,
                jsonb=detalhes,
                hash_anterior=anterior,
                hash_atual=hash_atual,
                assinatura=assinar(hash_atual.encode()),
                criado_em=ts,
            )
        )
        anterior = hash_atual


# ------- ÍNDICE DO E-MAIL -------------
# Sempre que o e-mail muda, o blind index acompanha (o e-mail em si é cifrado pelo tipo EmailCifrado)
@event.listens_for(entidades.Usuario.email, "set", retval=False)
def _atualizar_indice_email(usuario, valor, antigo, iniciador) -> None:
    usuario.email_indice = None if valor is None else indice_email(valor)
