from datetime import datetime
from uuid import UUID

from schemas.base import Entidade


class TentativaLogin(Entidade):
    id: int
    id_usuario: UUID
    nome_usuario_informado: str
    ip: str
    com_sucesso: bool
    motivo: str
    atualizado_em: datetime | None
