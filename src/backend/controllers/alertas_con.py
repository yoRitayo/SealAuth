from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import Alerta, AlertaCriar
from sqlalchemy.orm import Session
from controle_acesso import ChecadorPermissao


class AlertasController:
    def __init__(self):
        self.router = APIRouter(tags=["alertas"])
        self.router.add_api_route(
            "/alertas", self.criar_alerta, methods=["POST"],
            status_code=status.HTTP_201_CREATED, response_model=Alerta,
            dependencies=[Depends(ChecadorPermissao("gerenciar_bloqueios"))])
        self.router.add_api_route(
            "/usuarios/{id_usuario}/alertas", self.obter_alerta_usuario,
            methods=["GET"], response_model=list[Alerta],
            dependencies=[Depends(ChecadorPermissao("ler_alertas"))])

    async def criar_alerta(self, dados: AlertaCriar, db: Annotated[Session, Depends(obter_db)]):
        alerta = entidades.Alerta(
            **dados.model_dump(), criado_em=datetime.now(UTC))  # forma o dicionário com o dado
        db.add(alerta)
        db.commit()
        db.refresh(alerta)
        return alerta

    async def obter_alerta_usuario(self, id_usuario: UUID, db: Annotated[Session, Depends(obter_db)]):
        alertas = db.query(entidades.Alerta).filter(
            entidades.Alerta.id_usuario == id_usuario).all()
        if not alertas:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Alertas não encontrados")
        return alertas
