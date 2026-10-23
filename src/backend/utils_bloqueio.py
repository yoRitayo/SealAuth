"""Utilitários para gerenciamento de bloqueios de usuários."""
from datetime import UTC, datetime

from database import entidades
from sqlalchemy.orm import Session


def limpar_bloqueios_expirados(db: Session) -> int:
    """Remove bloqueios temporários que já expiraram.

    Returns:
        Número de usuários desbloqueados
    """
    try:
        agora = datetime.now(UTC)
        usuarios_bloqueados = db.query(entidades.Usuario).filter(
            entidades.Usuario.status == "bloqueado",
            entidades.Usuario.bloqueado_ate.isnot(None),
            entidades.Usuario.bloqueado_ate <= agora,
        ).all()

        for usuario in usuarios_bloqueados:
            usuario.status = "ativo"
            usuario.bloqueado_ate = None
            usuario.falhas_consecutivas = 0

        if usuarios_bloqueados:
            db.commit()

        return len(usuarios_bloqueados)
    except (AttributeError, Exception):
        return 0
