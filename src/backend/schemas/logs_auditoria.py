import base64
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import field_serializer

from schemas.base import Entidade


class LogAuditoria(Entidade):
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
