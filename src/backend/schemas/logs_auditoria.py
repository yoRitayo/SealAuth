import base64
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, field_serializer

from schemas.base import Entidade


class LogAuditoria(Entidade):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "id_usuario": "3f2a9c1e-8b7d-4e6f-9a1b-2c3d4e5f6a7b",
                    "evento": "login",
                    "ip": "127.0.0.1",
                    "jsonb": {},
                    "hash_anterior": "",
                    "hash_atual": "",
                    "assinatura": "",
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
