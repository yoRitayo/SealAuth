from datetime import datetime

from pydantic import BaseModel

from schemas.base import Entidade


class BloqueioIPCriar(BaseModel):
    id_alerta: int | None = None
    faixa: str


class BloqueioIPAtualizar(BaseModel):
    faixa: str | None = None
    expira_em: datetime | None = None


class BloqueioIP(Entidade):
    id: int
    id_alerta: int | None
    faixa: str
    criado_em: datetime
    expira_em: datetime
