# Hash de senha (argon2id), tokens JWT de acesso, refresh tokens e controle de acesso
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from config import JWT_ALGORITHM, JWT_EXPIRAMENTO_MINUTOS, JWT_SECRET
from database import entidades
from database.database import obter_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# ------- AUTENTICAÇÃO -------------
# PasswordHasher usa argon2id com parâmetros default
hasher = PasswordHasher()


def gerar_hash_senha(senha: str) -> str:
    return hasher.hash(senha)


def verificar_senha(senha_hash: str, senha: str) -> bool:
    try:
        return hasher.verify(senha_hash, senha)
    except (VerificationError, InvalidHashError):
        return False


# ------- REFRESH TOKEN -------------
def gerar_refresh_token() -> str:
    # 32 bytes de entropia (256 bits), codificados em base64url
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    # É o hash que vai para o Redis; o token em claro só existe no cookie do cliente
    return hashlib.sha256(token.encode()).hexdigest()


# ------- AUTORIZAÇÃO -------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def criar_token_acesso(usuario_id: UUID) -> str:
    agora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),  # subject
        "iat": agora,  # issued_at, quando o token foi emitido
        "exp": agora + timedelta(minutes=JWT_EXPIRAMENTO_MINUTOS),  # expiration
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    # Levanta jwt.InvalidTokenError se o token for inválido ou expirado
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def verificar_usuario(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(obter_db)],
) -> entidades.Usuario:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token(token)
        usuario_id = UUID(payload["sub"])
        if payload.get("type") != "access":
            raise credenciais_invalidas
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credenciais_invalidas

    usuario = db.get(entidades.Usuario, usuario_id)
    if usuario is None:
        raise credenciais_invalidas
    if usuario.status == "bloqueado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Conta bloqueada"
        )
    return usuario
