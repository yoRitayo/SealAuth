from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from schemas.base import Entidade


class TentativaLogin(Entidade):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "id_usuario": "3f2a9c1e-8b7d-4e6f-9a1b-2c3d4e5f6a7b",
                    "nome_usuario_informado": "ana",
                    "ip": "127.0.0.1",
                    "com_sucesso": True,
                    "motivo": "sucesso",
                    "atualizado_em": "2026-10-18T12:00:00Z",
                }
            ]
        }
    )
    id: int
    id_usuario: UUID | None
    nome_usuario_informado: str
    ip: str
    com_sucesso: bool
    motivo: str
    atualizado_em: datetime | None
