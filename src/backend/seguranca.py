# Hash de senha (argon2id) e criação/validação de JWT
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from config import JWT_ALGORITHM, JWT_EXPIRA_MINUTOS, JWT_SECRET
from database import entidades
from database.database import obter_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# ------- AUTENTICAÇÃO -------------
# PasswordHasher usa argon2id com parâmetros default (não estudei a fundo qual o impacto dos parâmetros então deixarei os padrões)
hasher = PasswordHasher()


def gerar_hash_senha(senha: str) -> str:
    return hasher.hash(senha)


def verificar_senha(senha_hash: str, senha: str) -> bool:
    try:
        return hasher.verify(senha_hash, senha)
    except (VerificationError, InvalidHashError):
        return False


# ------- AUTORIZAÇÃO  -------------

# Dependências do FastAPI para autorizar o usuário a partir do token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def criar_token(usuario_id: UUID) -> str:
    agora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),  # subject
        "iat": agora,  # issued_at, quando o token foi emitido
        "exp": agora + timedelta(minutes=JWT_EXPIRA_MINUTOS),  # expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    # Levanta jwt.InvalidTokenError se o token for inválido ou expirado
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def obter_usuario_atual(
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
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credenciais_invalidas

    usuario = db.get(entidades.Usuario, usuario_id)
    if usuario is None:
        raise credenciais_invalidas
    if usuario.status == "bloqueado":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Conta bloqueada")
    return usuario
