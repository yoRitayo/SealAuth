from typing import Annotated
from uuid import UUID

from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import Alerta, TentativaLogin, UsuarioPublico
from sqlalchemy.orm import Session


class UsuariosController:
    def __init__(self):
        self.router = APIRouter(tags=["usuarios"])
        self.router.add_api_route(
            "/usuarios/{senha_hash}", self.obter_usuario,
            methods=["GET"], response_model=UsuarioPublico)
        self.router.add_api_route(
            "/usuarios/{id_usuario}/alertas", self.obter_alerta_usuario,
            methods=["GET"], response_model=list[Alerta])
        self.router.add_api_route(
            "/usuarios/{id_usuario}/tentativas_login", self.obter_tentativas_login,
            methods=["GET"], response_model=list[TentativaLogin])

    async def obter_usuario(self, senha_hash: str, db: Annotated[Session, Depends(obter_db)]):
        usuario = db.query(entidades.Usuario).filter(
            entidades.Usuario.senha == senha_hash).first()
        if usuario is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Usuário não encontrado")
        return usuario

    async def obter_alerta_usuario(self, id_usuario: int, db: Annotated[Session, Depends(obter_db)]):
        alertas = db.query(entidades.Alerta).filter(
            entidades.Alerta.id_usuario == id_usuario).all()
        if not alertas:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Alertas não encontrados")
        return alertas

    async def obter_tentativas_login(self, id_usuario: UUID, db: Annotated[Session, Depends(obter_db)]):
        tentativas = db.query(entidades.TentativaLogin).filter(
            entidades.TentativaLogin.id_usuario == id_usuario).all()
        if not tentativas:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tentativas de login não encontradas")
        return tentativas
