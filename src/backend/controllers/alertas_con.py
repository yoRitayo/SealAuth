from datetime import UTC, datetime
from typing import Annotated

from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import Alerta, AlertaCriar, BloqueioIP
from sqlalchemy.orm import Session


class AlertasController:
    def __init__(self):
        self.router = APIRouter(tags=["alertas"])
        self.router.add_api_route(
            "/alertas", self.criar_alerta,
            methods=["POST"], status_code=status.HTTP_201_CREATED, response_model=Alerta)
        self.router.add_api_route(
            "/alertas/{id_alerta}", self.obter_alerta, methods=["GET"], response_model=list[Alerta])
        self.router.add_api_route(
            "/alertas/{id_alerta}/bloqueios_ip", self.obter_bloqueios_do_alerta,
            methods=["GET"], response_model=list[BloqueioIP])

    async def criar_alerta(self, dados: AlertaCriar, db: Annotated[Session, Depends(obter_db)]):
        alerta = entidades.Alerta(
            **dados.model_dump(), criado_em=datetime.now(UTC))  # forma o dicionário com o dado
        db.add(alerta)
        db.commit()
        db.refresh(alerta)
        return alerta

    async def obter_alerta(self, id_alerta: int, db: Annotated[Session, Depends(obter_db)]):
        alerta = db.query(entidades.Alerta).filter(
            entidades.Alerta.id == id_alerta).first()
        if not alerta:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Alerta não encontrados")
        return alerta

    async def obter_bloqueios_do_alerta(self, id_alerta: int, db: Annotated[Session, Depends(obter_db)]):
        bloqueios = db.query(entidades.BloqueioIP).filter(
            entidades.BloqueioIP.id_alerta == id_alerta).all()
        if not bloqueios:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bloqueios de IP não encontrados para este alerta")
        return bloqueios
