from typing import Annotated

from database import entidades
from fastapi import Depends, HTTPException, status
from seguranca import verificar_usuario

# Checagem de permissão (RBAC) usada como dependência nas rotas
PERMISSOES: dict[str, frozenset[str]] = {
    "admin": frozenset({"ler_perfil", "ler_logs", "ler_alertas", "gerenciar_usuarios", "gerenciar_bloqueios"}),
    "analista": frozenset({"ler_perfil", "ler_logs", "ler_alertas"}),
    "usuario": frozenset({"ler_perfil"}),
}


class ChecadorPermissao:
    def __init__(self, permissao: str):
        # Permissão exigida pela rota
        self.permissao = permissao

    def __call__(self, usuario: Annotated[entidades.Usuario, Depends(verificar_usuario)]) -> entidades.Usuario:
        permissoes_do_papel = PERMISSOES.get(usuario.papel, frozenset())
        if self.permissao not in permissoes_do_papel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para acessar este recurso.",
            )
        return usuario
