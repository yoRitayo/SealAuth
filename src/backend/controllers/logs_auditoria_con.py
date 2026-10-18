from typing import Annotated

from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends, status
from schemas import LogAuditoria
from sqlalchemy.orm import Session
from controle_acesso import ChecadorPermissao


class LogsAuditoriaController:
    def __init__(self):
        self.router = APIRouter(tags=["logs_auditoria"])
        self.router.add_api_route(
            "/logs-auditoria", self.listar_logs_auditoria, methods=["GET"],
            response_model=list[LogAuditoria],
            dependencies=[Depends(ChecadorPermissao("ler_logs"))])

    async def listar_logs_auditoria(self, db: Annotated[Session, Depends(obter_db)], pulo: int = 0, limite: int = 100) -> list[entidades.LogAuditoria]:
        return (
            db.query(entidades.LogAuditoria)
            # mais recente ao mais antigo
            .order_by(entidades.LogAuditoria.criado_em.desc())
            .offset(pulo)
            .limit(limite)
            .all()
        )
