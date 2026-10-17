from typing import Annotated

from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends
from schemas import LogAuditoria
from sqlalchemy.orm import Session


class LogsAuditoriaController:
    def __init__(self):
        self.router = APIRouter(tags=["logs_auditoria"])
        self.router.add_api_route(
            "/logs-auditoria", self.listar_logs_auditoria,
            methods=["GET"], response_model=list[LogAuditoria])

    async def listar_logs_auditoria(self, db: Annotated[Session, Depends(obter_db)], pulo: int = 0, limite: int = 100):
        return (
            db.query(entidades.LogAuditoria)
            # mais recente ao mais antigo
            .order_by(entidades.LogAuditoria.criado_em.desc())
            .offset(pulo)
            .limit(limite)
            .all()
        )
