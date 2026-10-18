from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

import redis
from config import (
    COOKIE_SECURE,
    JANELA_RATE_LIMIT_SEGUNDOS,
    LIMITE_FALHAS_LOGIN,
    LIMITE_REQUISICOES_LOGIN,
    MINUTOS_BLOQUEIO_LOGIN,
    REFRESH_TOKEN_EXPIRAMENTO_DIAS,
)
from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from redis_cliente import (
    criar_sessao,
    revogar_familia,
    revogar_sessao,
    revogar_todas_sessoes,
    rotacionar_sessao,
    verificar_rate_limit,
)
from schemas import Token
from seguranca import criar_token_acesso, verificar_senha
from sqlalchemy.orm import Session

NOME_COOKIE = "refresh_token"
CAMINHO_COOKIE = "/auth"  # o cookie só é enviado às rotas de autenticação


def _indisponivel() -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                         detail="Serviço de autenticação indisponível")


def _definir_cookie(resposta: Response, token: str) -> None:
    # HttpOnly: o JavaScript não lê. SameSite strict: não é enviado em requisições cross-site
    resposta.set_cookie(
        key=NOME_COOKIE,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path=CAMINHO_COOKIE,
        max_age=REFRESH_TOKEN_EXPIRAMENTO_DIAS * 24 * 60 * 60,
    )


class AuthController:
    def __init__(self):
        self.router = APIRouter(tags=["auth"])
        self.router.add_api_route(
            "/auth/login", self.login, methods=["POST"], response_model=Token)
        self.router.add_api_route(
            "/auth/refresh", self.refresh, methods=["POST"], response_model=Token)
        self.router.add_api_route(
            "/auth/logout", self.logout, methods=["POST"], status_code=status.HTTP_204_NO_CONTENT)

    # Formulário OAuth2 (o "Authorize" do Swagger)
    async def login(self, requisicao: Request, resposta: Response,
                    formulario: Annotated[OAuth2PasswordRequestForm, Depends()],
                    db: Annotated[Session, Depends(obter_db)]) -> Token:
        agora = datetime.now(UTC)
        ip = requisicao.client.host if requisicao.client else "0.0.0.0"
        credenciais_invalidas = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

        # Rate limit por IP e por nome de usuário (vale até para usuários inexistentes)
        try:
            dentro_do_limite_ip = verificar_rate_limit(
                f"rl:login:ip:{ip}", LIMITE_REQUISICOES_LOGIN, JANELA_RATE_LIMIT_SEGUNDOS)
            dentro_do_limite_usuario = verificar_rate_limit(
                f"rl:login:usuario:{formulario.username.lower()}",
                LIMITE_REQUISICOES_LOGIN, JANELA_RATE_LIMIT_SEGUNDOS)
        except redis.RedisError:
            raise _indisponivel()
        if not (dentro_do_limite_ip and dentro_do_limite_usuario):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Muitas tentativas. Aguarde um minuto.",
                                headers={"Retry-After": str(JANELA_RATE_LIMIT_SEGUNDOS)})

        usuario = db.query(entidades.Usuario).filter(
            entidades.Usuario.nome_usuario == formulario.username).first()
        if usuario is None:
            raise credenciais_invalidas

        if usuario.status == "bloqueado":
            if usuario.bloqueado_ate is not None and usuario.bloqueado_ate <= agora:
                # Bloqueio temporário expirou
                usuario.status = "ativo"
                usuario.bloqueado_ate = None
                usuario.falhas_consecutivas = 0
            else:
                self._registrar_tentativa(
                    db, usuario, formulario.username, ip, False, "conta_bloqueada", agora)
                db.commit()
                raise HTTPException(status_code=status.HTTP_423_LOCKED,
                                    detail="Conta bloqueada")

        if not verificar_senha(usuario.senha, formulario.password):
            usuario.falhas_consecutivas += 1
            if usuario.falhas_consecutivas >= LIMITE_FALHAS_LOGIN:
                usuario.status = "bloqueado"
                usuario.bloqueado_ate = agora + \
                    timedelta(minutes=MINUTOS_BLOQUEIO_LOGIN)
            self._registrar_tentativa(
                db, usuario, formulario.username, ip, False, "senha_incorreta", agora)
            db.commit()
            raise credenciais_invalidas

        usuario.falhas_consecutivas = 0
        self._registrar_tentativa(
            db, usuario, formulario.username, ip, True, "sucesso", agora)
        db.commit()

        # Sessão única: um novo login derruba as sessões anteriores da conta
        try:
            revogar_todas_sessoes(usuario.id)
            refresh_token = criar_sessao(usuario.id, familia=str(uuid4()))
        except redis.RedisError:
            raise _indisponivel()
        _definir_cookie(resposta, refresh_token)
        return Token(access_token=criar_token_acesso(usuario.id))

    async def refresh(self, resposta: Response, db: Annotated[Session, Depends(obter_db)],
                      refresh_token: Annotated[str | None, Cookie(alias=NOME_COOKIE)] = None) -> Token:
        nao_autorizado = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada",
            headers={"WWW-Authenticate": "Bearer"},
        )
        if not refresh_token:
            raise nao_autorizado

        try:
            estado, familia, usuario_id, novo_token = rotacionar_sessao(
                refresh_token)
        except redis.RedisError:
            raise _indisponivel()
        if estado != "ok" or novo_token is None:
            # reuso, revogada ou inexistente: não renova
            raise nao_autorizado

        usuario = db.get(entidades.Usuario, UUID(usuario_id))
        if usuario is None or usuario.status == "bloqueado":
            revogar_familia(familia)
            raise nao_autorizado

        _definir_cookie(resposta, novo_token)
        return Token(access_token=criar_token_acesso(usuario.id))

    async def logout(self, resposta: Response,
                     refresh_token: Annotated[str | None, Cookie(alias=NOME_COOKIE)] = None) -> None:
        if refresh_token:
            try:
                revogar_sessao(refresh_token)
            except redis.RedisError:
                raise _indisponivel()
        resposta.delete_cookie(key=NOME_COOKIE, path=CAMINHO_COOKIE,
                               httponly=True, secure=COOKIE_SECURE, samesite="strict")

    @staticmethod
    def _registrar_tentativa(db: Session, usuario: entidades.Usuario, nome_informado: str,
                             ip: str, com_sucesso: bool, motivo: str, agora: datetime) -> None:
        db.add(entidades.TentativaLogin(
            id_usuario=usuario.id,
            nome_usuario_informado=nome_informado,
            ip=ip,
            com_sucesso=com_sucesso,
            motivo=motivo,
            atualizado_em=agora,
        ))
