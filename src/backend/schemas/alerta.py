import base64
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from schemas.base import Entidade


class AlertaCriar(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id_usuario": "3f2a9c1e-8b7d-4e6f-9a1b-2c3d4e5f6a7b",
                    "evento": "login_suspeito",
                    "ip": "203.0.113.7",
                    "jsonb": {"tentativas": 7},
                    "hash_anterior": "a1b2",
                    "hash_atual": "c3d4",
                    "assinatura": "c2Fzc2luYXR1cmEtZW0tYmFzZTY0",
                }
            ]
        }
    )
    id_usuario: UUID
    evento: str
    ip: str
    jsonb: dict[str, Any]
    hash_anterior: str
    hash_atual: str
    assinatura: bytes

    @field_validator("assinatura", mode="before")
    @classmethod
    def _decodificar_assinatura(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            return base64.b64decode(valor)
        return valor


class Alerta(Entidade):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "id_usuario": "3f2a9c1e-8b7d-4e6f-9a1b-2c3d4e5f6a7b",
                    "evento": "login_suspeito",
                    "ip": "203.0.113.7",
                    "jsonb": {"tentativas": 7},
                    "hash_anterior": "a1b2",
                    "hash_atual": "c3d4",
                    "assinatura": "c2Fzc2luYXR1cmEtZW0tYmFzZTY0",
                    "criado_em": "2026-10-18T12:00:00Z",
                }
            ]
        }
    )
    id: int
    id_usuario: UUID | None
    evento: str
    ip: str
    jsonb: dict[str, Any]
    hash_anterior: str
    hash_atual: str
    assinatura: bytes
    criado_em: datetime

    @field_serializer("assinatura")
    def _serializar_assinatura(self, valor: bytes) -> str:
        return base64.b64encode(valor).decode()
