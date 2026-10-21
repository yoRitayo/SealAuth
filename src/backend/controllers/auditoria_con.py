from typing import Annotated, Any

from auditoria import verificar_cadeia
from controle_acesso import ChecadorPermissao
from database.database import obter_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session


class AuditoriaController:
    def __init__(self):
        self.router = APIRouter(tags=["logs_auditoria"])
        self.router.add_api_route(
            "/logs-auditoria/verificar",
            self.verificar_logs,
            methods=["GET"],
            dependencies=[Depends(ChecadorPermissao("ler_logs"))],
        )

    # Recalcula a cadeia SHA-256 e confere a assinatura RSA de cada entrada
    async def verificar_logs(
        self, db: Annotated[Session, Depends(obter_db)]
    ) -> dict[str, Any]:
        return verificar_cadeia(db)
