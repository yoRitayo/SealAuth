# Dependências do FastAPI para identificar o usuário a partir do token
from typing import Annotated
from uuid import UUID

import jwt
from database import entidades
from database.database import obter_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from seguranca import decodificar_token
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


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
