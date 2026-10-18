from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.base import Entidade


class BloqueioIPCriar(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"id_alerta": 1, "faixa": "203.0.113.0/24", "expira_em": "2026-10-19T12:00:00Z"}]})
    id_alerta: int | None = None
    faixa: str


class BloqueioIPAtualizar(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"expira_em": "2026-10-20T12:00:00Z"}]})
    faixa: str | None = None
    expira_em: datetime | None = None


class BloqueioIP(Entidade):
    model_config = ConfigDict(json_schema_extra={"examples": [{"id": 1, "id_alerta": 1, "faixa": "203.0.113.0/24", "criado_em": "2026-10-18T12:00:00Z", "expira_em": "2026-10-19T12:00:00Z"}]})
    id: int
    id_alerta: int | None
    faixa: str
    criado_em: datetime
    expira_em: datetime
