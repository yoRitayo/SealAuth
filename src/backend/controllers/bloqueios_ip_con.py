from datetime import UTC, datetime
from typing import Annotated

from controle_acesso import ChecadorPermissao
from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import BloqueioIP, BloqueioIPAtualizar, BloqueioIPCriar
from sqlalchemy.orm import Session


class BloqueiosIPController:
    def __init__(self):
        self.router = APIRouter(tags=["bloqueios_ip"])
        self.router.add_api_route(
            "/bloqueios_ip",
            self.criar_bloqueio_ip,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            response_model=BloqueioIP,
            dependencies=[Depends(ChecadorPermissao("gerenciar_bloqueios"))],
        )
        self.router.add_api_route(
            "/bloqueios_ip",
            self.listar_bloqueios_ip,
            methods=["GET"],
            response_model=list[BloqueioIP],
            dependencies=[Depends(ChecadorPermissao("ler_alertas"))],
        )
        self.router.add_api_route(
            "/bloqueios_ip/{id_bloqueio}",
            self.obter_bloqueio_ip,
            methods=["GET"],
            response_model=list[BloqueioIP],
            dependencies=[Depends(ChecadorPermissao("ler_alertas"))],
        )
        self.router.add_api_route(
            "/alertas/{id_alerta}/bloqueios_ip",
            self.obter_bloqueios_do_alerta,
            methods=["GET"],
            response_model=list[BloqueioIP],
            dependencies=[Depends(ChecadorPermissao("ler_alertas"))],
        )
        self.router.add_api_route(
            "/bloqueios_ip/{id_bloqueio}",
            self.atualizar_bloqueio_ip,
            methods=["PATCH"],
            response_model=BloqueioIP,
            dependencies=[Depends(ChecadorPermissao("gerenciar_bloqueios"))],
        )

    async def criar_bloqueio_ip(
        self, dados: BloqueioIPCriar, db: Annotated[Session, Depends(obter_db)]
    ) -> entidades.BloqueioIP:
        bloqueio = entidades.BloqueioIP(
            **dados.model_dump(), criado_em=datetime.now(UTC)
        )
        db.add(bloqueio)
        db.commit()
        db.refresh(bloqueio)
        return bloqueio

    async def listar_bloqueios_ip(
        self,
        db: Annotated[Session, Depends(obter_db)],
        pulo: int = 0,
        limite: int = 100,
    ) -> list[entidades.BloqueioIP]:
        return (
            db.query(entidades.BloqueioIP)
            .order_by(entidades.BloqueioIP.criado_em.desc())
            .offset(pulo)
            .limit(limite)
            .all()
        )

    async def obter_bloqueio_ip(
        self, id_bloqueio: int, db: Annotated[Session, Depends(obter_db)]
    ) -> list[entidades.BloqueioIP]:
        bloqueios = (
            db.query(entidades.BloqueioIP)
            .filter(entidades.BloqueioIP.id == id_bloqueio)
            .all()
        )
        if not bloqueios:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bloqueios de IP não encontrados",
            )
        return bloqueios

    async def obter_bloqueios_do_alerta(
        self, id_alerta: int, db: Annotated[Session, Depends(obter_db)]
    ) -> list[entidades.BloqueioIP]:
        bloqueios = (
            db.query(entidades.BloqueioIP)
            .filter(entidades.BloqueioIP.id_alerta == id_alerta)
            .all()
        )
        if not bloqueios:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bloqueios de IP não encontrados para este alerta",
            )
        return bloqueios

    async def atualizar_bloqueio_ip(
        self,
        id_bloqueio: int,
        dados: BloqueioIPAtualizar,
        db: Annotated[Session, Depends(obter_db)],
    ) -> entidades.BloqueioIP:
        bloqueio = (
            db.query(entidades.BloqueioIP)
            .filter(entidades.BloqueioIP.id == id_bloqueio)
            .with_for_update()
            .first()
        )
        if bloqueio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bloqueio de IP não encontrado",
            )
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(bloqueio, campo, valor)
        db.commit()
        db.refresh(bloqueio)
        return bloqueio
