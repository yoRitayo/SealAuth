from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from controle_acesso import PERMISSOES, ChecadorPermissao
from database import entidades
from database.database import obter_db
from fastapi import APIRouter, Depends, HTTPException, Response, status
from schemas import (
    Usuario,
    UsuarioAtualizarNome,
    UsuarioAtualizarPapel,
    UsuarioAtualizarSenha,
    UsuarioCriar,
)
from redis_cliente import revogar_todas_sessoes
from seguranca import gerar_hash_senha, verificar_senha, verificar_usuario
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _pode_gerenciar_usuarios(usuario: entidades.Usuario) -> bool:
    return "gerenciar_usuarios" in PERMISSOES.get(usuario.papel, frozenset())


def _buscar_usuario(db: Session, id_usuario: UUID) -> entidades.Usuario:
    usuario = db.get(entidades.Usuario, id_usuario)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuário não encontrado")
    return usuario


def _nao_pode_ser_o_proprio_admin(admin: entidades.Usuario, alvo: entidades.Usuario, acao: str) -> None:
    # Evita que o admin se tranque para fora do sistema
    if admin.id == alvo.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Você não pode {acao} a si mesmo")


class UsuariosController:
    def __init__(self):
        self.router = APIRouter(tags=["usuarios"])
        self.router.add_api_route(
            "/usuarios", self.criar_usuario,
            methods=["POST"], status_code=status.HTTP_201_CREATED, response_model=Usuario)
        self.router.add_api_route(
            "/usuarios/{id_usuario}", self.obter_usuario,
            methods=["GET"], response_model=Usuario)
        self.router.add_api_route(
            "/usuarios/{id_usuario}/nome_usuario", self.atualizar_nome_usuario,
            methods=["PATCH"], response_model=Usuario)
        self.router.add_api_route(
            "/usuarios/{id_usuario}/senha", self.atualizar_senha,
            methods=["PATCH"], response_model=Usuario)
        self.router.add_api_route(
            "/usuarios/{id_usuario}/papel", self.atualizar_papel,
            methods=["PATCH"], response_model=Usuario)
        self.router.add_api_route(
            "/usuarios/{id_usuario}/bloquear", self.bloquear_usuario,
            methods=["POST"], response_model=Usuario)
        self.router.add_api_route(
            "/usuarios/{id_usuario}/desbloquear", self.desbloquear_usuario,
            methods=["POST"], response_model=Usuario)
        self.router.add_api_route(
            "/usuarios/{id_usuario}", self.deletar_usuario,
            methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT)

    async def criar_usuario(self, dados: UsuarioCriar, db: Annotated[Session, Depends(obter_db)]) -> entidades.Usuario:
        usuario = entidades.Usuario(
            id=uuid4(),
            nome_usuario=dados.nome_usuario,
            email=dados.email.encode(),  # LargeBinary por enquanto
            senha=gerar_hash_senha(dados.senha),
            papel="usuario",
            status="ativo",
            falhas_consecutivas=0,
            bloqueado_ate=None,
            criado_em=datetime.now(UTC),
        )
        db.add(usuario)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Nome de usuário já existe")
        db.refresh(usuario)
        return usuario

    async def obter_usuario(self, id_usuario: UUID, db: Annotated[Session, Depends(obter_db)],
                            usuario_atual: Annotated[entidades.Usuario, Depends(ChecadorPermissao("ler_perfil"))]) -> entidades.Usuario:
        if usuario_atual.id != id_usuario and not _pode_gerenciar_usuarios(usuario_atual):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Você só pode ver o próprio perfil")
        return _buscar_usuario(db, id_usuario)

    # Só o próprio usuário altera o nome
    async def atualizar_nome_usuario(self, id_usuario: UUID, dados: UsuarioAtualizarNome,
                                     db: Annotated[Session, Depends(obter_db)],
                                     usuario_atual: Annotated[entidades.Usuario, Depends(verificar_usuario)]) -> entidades.Usuario:
        if usuario_atual.id != id_usuario:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Você só pode alterar o próprio nome")
        usuario_atual.nome_usuario = dados.nome_usuario
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Nome de usuário já existe")
        db.refresh(usuario_atual)
        return usuario_atual

    # Só o próprio usuário altera a senha, informando a atual
    async def atualizar_senha(self, id_usuario: UUID, dados: UsuarioAtualizarSenha,
                              db: Annotated[Session, Depends(obter_db)],
                              usuario_atual: Annotated[entidades.Usuario, Depends(verificar_usuario)]) -> entidades.Usuario:
        if usuario_atual.id != id_usuario:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Você só pode alterar a própria senha")
        if not verificar_senha(usuario_atual.senha, dados.senha_atual):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Senha atual incorreta")
        usuario_atual.senha = gerar_hash_senha(dados.nova_senha)
        db.commit()
        revogar_todas_sessoes(usuario_atual.id)  # troca de senha derruba todas as sessões
        db.refresh(usuario_atual)
        return usuario_atual

    async def atualizar_papel(self, id_usuario: UUID, dados: UsuarioAtualizarPapel,
                              db: Annotated[Session, Depends(obter_db)],
                              admin: Annotated[entidades.Usuario, Depends(ChecadorPermissao("gerenciar_usuarios"))]) -> entidades.Usuario:
        usuario = _buscar_usuario(db, id_usuario)
        _nao_pode_ser_o_proprio_admin(admin, usuario, "alterar o papel de")
        usuario.papel = dados.papel
        db.commit()
        db.refresh(usuario)
        return usuario

    async def bloquear_usuario(self, id_usuario: UUID, db: Annotated[Session, Depends(obter_db)],
                               admin: Annotated[entidades.Usuario, Depends(ChecadorPermissao("gerenciar_usuarios"))]) -> entidades.Usuario:
        usuario = _buscar_usuario(db, id_usuario)
        _nao_pode_ser_o_proprio_admin(admin, usuario, "bloquear")
        # Bloqueio manual: sem bloqueado_ate, só o admin desbloqueia
        usuario.status = "bloqueado"
        usuario.bloqueado_ate = None
        db.commit()
        revogar_todas_sessoes(usuario.id)
        db.refresh(usuario)
        return usuario

    async def desbloquear_usuario(self, id_usuario: UUID, db: Annotated[Session, Depends(obter_db)],
                                  admin: Annotated[entidades.Usuario, Depends(ChecadorPermissao("gerenciar_usuarios"))]) -> entidades.Usuario:
        usuario = _buscar_usuario(db, id_usuario)
        usuario.status = "ativo"
        usuario.bloqueado_ate = None
        usuario.falhas_consecutivas = 0
        db.commit()
        db.refresh(usuario)
        return usuario

    async def deletar_usuario(self, id_usuario: UUID, db: Annotated[Session, Depends(obter_db)],
                              admin: Annotated[entidades.Usuario, Depends(ChecadorPermissao("gerenciar_usuarios"))]) -> Response:
        usuario = _buscar_usuario(db, id_usuario)
        _nao_pode_ser_o_proprio_admin(admin, usuario, "deletar")
        db.delete(usuario)
        db.commit()
        revogar_todas_sessoes(id_usuario)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
