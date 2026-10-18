from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from schemas.base import Entidade

Papel = Literal["admin", "analista", "usuario"]
Status = Literal["ativo", "bloqueado"]


class Usuario(Entidade):
    id: UUID
    nome_usuario: str
    papel: Papel
    status: Status
    falhas_consecutivas: int
    bloqueado_ate: datetime | None
    criado_em: datetime


class UsuarioCriar(BaseModel):
    nome_usuario: str
    email: str
    senha: str


class UsuarioAtualizarNome(BaseModel):
    nome_usuario: str


class UsuarioAtualizarSenha(BaseModel):
    senha_atual: str
    nova_senha: str


class UsuarioAtualizarPapel(BaseModel):
    papel: Papel


# O refresh token fica em um cookie HttpOnly
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
