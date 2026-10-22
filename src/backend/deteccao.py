# DetectionService: regras do IDS sobre as tentativas de login e resposta do IPS
# (bloqueio de IP no firewall da aplicação). Limiares iniciais da Tabela 9 do documento.
import ipaddress
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from auditoria import calcular_hash, ip_requisicao
from config import LIMITE_FALHAS_LOGIN
from cripto import assinar
from database import entidades
from database.database import obter_db
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import cast, func, or_, select
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Session

# ------- LIMIARES -------------
FALHAS_CONTA_SUSPEITA = 3  # estado "Suspeita" (T2): alerta de baixa severidade
JANELA_DETECCAO = timedelta(minutes=5)
LIMITE_USUARIOS_POR_IP = 10  # credential stuffing: usuários diferentes do mesmo IP
LIMITE_USUARIOS_INEXISTENTES = 5  # enumeração: logins de usuários que não existem
MINUTOS_BLOQUEIO_IP = 30
JANELA_ALERTA_EXCESSO = timedelta(minutes=1)  # um alerta de 429 por IP a cada minuto

MOTIVO_USUARIO_INEXISTENTE = "usuario_inexistente"


def _ip_valido(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


# ------- FIREWALL -------------
def ip_bloqueado(db: Session, ip: str) -> bool:
    # O IP de origem está em alguma faixa bloqueada e ainda não expirada?
    if not _ip_valido(ip):
        return False
    agora = datetime.now(UTC)
    consulta = (
        select(entidades.BloqueioIP.id)
        .where(entidades.BloqueioIP.faixa.op(">>=")(cast(ip, INET)))
        .where(
            or_(
                entidades.BloqueioIP.expira_em.is_(None),
                entidades.BloqueioIP.expira_em > agora,
            )
        )
        .limit(1)
    )
    return db.scalar(consulta) is not None


def verificar_firewall(
    requisicao: Request, db: Annotated[Session, Depends(obter_db)]
) -> None:
    # Primeira barreira de todas as rotas (dependência global em main.py)
    ip = requisicao.client.host if requisicao.client else "0.0.0.0"
    if ip_bloqueado(db, ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acesso bloqueado"
        )


# ------- ALERTAS E BLOQUEIOS -------------
def registrar_alerta(
    db: Session,
    regra: str,
    severidade: str,
    ip: str,
    descricao: str,
    id_usuario: UUID | None = None,
    **detalhes: Any,
) -> entidades.Alerta:
    # O alerta reaproveita as colunas existentes: evento = regra, jsonb = severidade e detalhes.
    # Cada alerta é assinado individualmente; a cadeia fica no log de auditoria (alerta_criado).
    agora = datetime.now(UTC)
    jsonb = {"severidade": severidade, "descricao": descricao, **detalhes}
    hash_atual = calcular_hash("", agora, id_usuario, regra, ip, jsonb)
    alerta = entidades.Alerta(
        id_usuario=id_usuario,
        evento=regra,
        ip=ip,
        jsonb=jsonb,
        hash_anterior="",
        hash_atual=hash_atual,
        assinatura=assinar(hash_atual.encode()),
        criado_em=agora,
    )
    db.add(alerta)
    return alerta


def bloquear_ip(db: Session, ip: str, alerta: entidades.Alerta) -> entidades.BloqueioIP:
    # Resposta do IPS: a faixa /32 (ou /128) do IP entra na lista do firewall
    agora = datetime.now(UTC)
    bloqueio = entidades.BloqueioIP(
        alerta=alerta,
        faixa=str(ipaddress.ip_network(ip)),
        criado_em=agora,
        expira_em=agora + timedelta(minutes=MINUTOS_BLOQUEIO_IP),
    )
    db.add(bloqueio)
    return bloqueio


# ------- REGRAS DO IDS -------------
def _contar_tentativas(db: Session, ip: str, *filtros: Any, distintos: bool = False) -> int:
    desde = datetime.now(UTC) - JANELA_DETECCAO
    contagem = (
        func.count(entidades.TentativaLogin.nome_usuario_informado.distinct())
        if distintos
        else func.count()
    )
    consulta = (
        select(contagem)
        .select_from(entidades.TentativaLogin)
        .where(entidades.TentativaLogin.ip == ip)
        .where(entidades.TentativaLogin.atualizado_em >= desde)
        .where(*filtros)
    )
    return db.scalar(consulta) or 0


def analisar_falha_login(
    db: Session, ip: str, usuario: entidades.Usuario | None, motivo: str
) -> None:
    # Chamada pelo login depois de registrar a tentativa, antes do commit
    if not _ip_valido(ip):
        return
    db.flush()  # a tentativa atual entra nas contagens

    if usuario is not None and motivo == "senha_incorreta":
        if usuario.falhas_consecutivas == FALHAS_CONTA_SUSPEITA:
            registrar_alerta(
                db, "conta_suspeita", "baixa", ip,
                f"{FALHAS_CONTA_SUSPEITA} falhas consecutivas na conta",
                usuario.id, falhas=usuario.falhas_consecutivas,
            )
        elif usuario.falhas_consecutivas == LIMITE_FALHAS_LOGIN:
            registrar_alerta(
                db, "forca_bruta", "alta", ip,
                f"{LIMITE_FALHAS_LOGIN} falhas consecutivas: conta bloqueada",
                usuario.id, falhas=usuario.falhas_consecutivas,
            )

    if motivo == MOTIVO_USUARIO_INEXISTENTE:
        inexistentes = _contar_tentativas(
            db, ip, entidades.TentativaLogin.motivo == MOTIVO_USUARIO_INEXISTENTE
        )
        # Igualdade: alerta uma vez, quando o limiar é atingido
        if inexistentes == LIMITE_USUARIOS_INEXISTENTES:
            registrar_alerta(
                db, "enumeracao", "media", ip,
                f"{inexistentes} logins de usuários inexistentes em 5 min",
                tentativas=inexistentes,
            )

    usuarios = _contar_tentativas(
        db, ip, entidades.TentativaLogin.com_sucesso.is_(False), distintos=True
    )
    if usuarios >= LIMITE_USUARIOS_POR_IP and not ip_bloqueado(db, ip):
        alerta = registrar_alerta(
            db, "credential_stuffing", "alta", ip,
            f"{usuarios} usuários diferentes em 5 min: IP bloqueado por {MINUTOS_BLOQUEIO_IP} min",
            usuarios=usuarios,
        )
        bloquear_ip(db, ip, alerta)


def alertar_excesso_requisicoes(db: Session, ip: str) -> None:
    # Acompanha o 429 do rate limit; não repete o alerta do mesmo IP dentro da janela
    if not _ip_valido(ip):
        return
    desde = datetime.now(UTC) - JANELA_ALERTA_EXCESSO
    ja_alertado = db.scalar(
        select(func.count())
        .select_from(entidades.Alerta)
        .where(entidades.Alerta.evento == "excesso_requisicoes")
        .where(entidades.Alerta.ip == ip)
        .where(entidades.Alerta.criado_em >= desde)
    )
    if not ja_alertado:
        registrar_alerta(
            db, "excesso_requisicoes", "media", ip,
            "Limite de tentativas de login por minuto excedido",
        )


def alertar_token_invalido(db: Session, motivo: str) -> None:
    # JWT com assinatura inválida ou algoritmo trocado: indício de token forjado
    ip = ip_requisicao.get() or "0.0.0.0"
    if not _ip_valido(ip):
        ip = "0.0.0.0"
    registrar_alerta(db, "token_invalido", "alta", ip, "JWT com assinatura inválida", motivo=motivo)
    db.commit()
