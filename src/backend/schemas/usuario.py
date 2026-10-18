from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from schemas.base import Entidade

Papel = Literal["admin", "analista", "usuario"]
Status = Literal["pendente", "ativo", "bloqueado"]


class Usuario(Entidade):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "3f2a9c1e-8b7d-4e6f-9a1b-2c3d4e5f6a7b",
                    "nome_usuario": "ana",
                    "papel": "usuario",
                    "status": "ativo",
                    "falhas_consecutivas": 0,
                    "bloqueado_ate": None,
                    "criado_em": "2026-10-18T12:00:00Z",
                }
            ]
        }
    )
    id: UUID
    nome_usuario: str
    papel: Papel
    status: Status
    falhas_consecutivas: int
    bloqueado_ate: datetime | None
    criado_em: datetime


class UsuarioCriar(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome_usuario": "ana",
                    "email": "ana@exemplo.com",
                    "senha": "senha-forte-123",
                }
            ]
        }
    )
    nome_usuario: str
    email: str
    senha: str


class UsuarioAtualizarNome(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"nome_usuario": "ana.silva"}]}
    )
    nome_usuario: str


class UsuarioAtualizarSenha(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"senha_atual": "senha-forte-123", "nova_senha": "nova-senha-456"}
            ]
        }
    )
    senha_atual: str
    nova_senha: str


class UsuarioAtualizarPapel(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"papel": "analista"}]})
    papel: Papel


class EsqueciSenha(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "ana@exemplo.com"}]}
    )
    email: str


class RedefinirSenha(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"token": "token-recebido-por-email",
                    "nova_senha": "nova-senha-456"}
            ]
        }
    )
    token: str
    nova_senha: str


class AtivarConta(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"token": "token-recebido-por-email"}]}
    )
    token: str


class ReenviarAtivacao(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "ana@exemplo.com"}]}
    )
    email: str


# O refresh token fica em um cookie HttpOnly
class Token(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.exemplo.assinatura",
                    "token_type": "bearer",
                }
            ]
        }
    )
    access_token: str
    token_type: str = "bearer"
