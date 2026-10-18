from typing import Annotated
from uuid import UUID

from controle_acesso import ChecadorPermissao
from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import TentativaLogin
from sqlalchemy.orm import Session


class TentativasLoginController:
    def __init__(self):
        self.router = APIRouter(tags=["tentativas_login"])
        self.router.add_api_route(
            "/usuarios/{id_usuario}/tentativas_login", self.obter_tentativas_login,
            methods=["GET"], response_model=list[TentativaLogin],
            dependencies=[Depends(ChecadorPermissao("ler_logs"))])

    async def obter_tentativas_login(self, id_usuario: UUID, db: Annotated[Session, Depends(obter_db)]) -> list[entidades.TentativaLogin]:
        tentativas = db.query(entidades.TentativaLogin).filter(
            entidades.TentativaLogin.id_usuario == id_usuario).all()
        if not tentativas:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tentativas de login não encontradas")
        return tentativas
