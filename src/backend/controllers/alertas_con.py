import base64
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from auditoria import calcular_hash
from controle_acesso import ChecadorPermissao
from cripto import assinar
from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from schemas import Alerta, AlertaCriar
from sqlalchemy.orm import Session


class DadosAlertaParaAssinar(BaseModel):
    id_usuario: UUID
    evento: str
    ip: str
    jsonb: dict[str, Any]
    hash_anterior: str


class ResultadoAssinatura(BaseModel):
    hash_atual: str
    assinatura: str


class AlertasController:
    def __init__(self):
        self.router = APIRouter(tags=["alertas"])
        self.router.add_api_route(
            "/alertas/gerar-assinatura",
            self.gerar_assinatura,
            methods=["POST"],
            response_model=ResultadoAssinatura,
            dependencies=[Depends(ChecadorPermissao("gerenciar_bloqueios"))],
        )
        self.router.add_api_route(
            "/alertas",
            self.criar_alerta,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            response_model=Alerta,
            dependencies=[Depends(ChecadorPermissao("gerenciar_bloqueios"))],
        )
        self.router.add_api_route(
            "/alertas",
            self.listar_alertas,
            methods=["GET"],
            response_model=list[Alerta],
            dependencies=[Depends(ChecadorPermissao("ler_alertas"))],
        )
        self.router.add_api_route(
            "/usuarios/{id_usuario}/alertas",
            self.obter_alerta_usuario,
            methods=["GET"],
            response_model=list[Alerta],
            dependencies=[Depends(ChecadorPermissao("ler_alertas"))],
        )

    async def listar_alertas(
        self,
        db: Annotated[Session, Depends(obter_db)],
        pulo: int = 0,
        limite: int = 100,
    ) -> list[entidades.Alerta]:
        return (
            db.query(entidades.Alerta)
            .order_by(entidades.Alerta.criado_em.desc())
            .offset(pulo)
            .limit(limite)
            .all()
        )

    async def gerar_assinatura(
        self, dados: DadosAlertaParaAssinar
    ) -> ResultadoAssinatura:
        hash_atual = calcular_hash(
            hash_anterior=dados.hash_anterior,
            ts=datetime.now(UTC),
            id_usuario=dados.id_usuario,
            evento=dados.evento,
            ip=dados.ip,
            detalhes=dados.jsonb,
        )
        assinatura_bytes = assinar(hash_atual.encode())
        assinatura_base64 = base64.b64encode(assinatura_bytes).decode()
        return ResultadoAssinatura(
            hash_atual=hash_atual, assinatura=assinatura_base64
        )

    async def criar_alerta(
        self, dados: AlertaCriar, db: Annotated[Session, Depends(obter_db)]
    ) -> entidades.Alerta:
        alerta = entidades.Alerta(
            **dados.model_dump(), criado_em=datetime.now(UTC)
        )  # forma o dicionário com o dado
        db.add(alerta)
        db.commit()
        db.refresh(alerta)
        return alerta

    async def obter_alerta_usuario(
        self, id_usuario: UUID, db: Annotated[Session, Depends(obter_db)]
    ) -> list[entidades.Alerta]:
        alertas = (
            db.query(entidades.Alerta)
            .filter(entidades.Alerta.id_usuario == id_usuario)
            .all()
        )
        if not alertas:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Alertas não encontrados"
            )
        return alertas
