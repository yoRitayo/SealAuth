import base64
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_serializer, field_validator

from schemas.base import Entidade


class AlertaCriar(BaseModel):
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
    id: int
    id_usuario: UUID
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
