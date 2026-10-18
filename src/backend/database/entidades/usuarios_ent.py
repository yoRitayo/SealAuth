from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from database.database import Base
from sqlalchemy import DateTime, Integer, LargeBinary, Text, Uuid
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from database.entidades.logs_auditoria_ent import LogAuditoria
    from database.entidades.tentativas_login_ent import TentativaLogin


class Usuario(Base):
    """Tabela de usuários 

    Args:
        Base: cria automaticamente um dicionário Python que armazena uma série de 
        objetos Table chaveados para sua string nome. 
    """
    __tablename__ = "USUARIOS"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    nome_usuario: Mapped[str] = mapped_column(CITEXT, unique=True)
    email: Mapped[str] = mapped_column(LargeBinary)
    senha: Mapped[str] = mapped_column(Text)
    papel: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    falhas_consecutivas: Mapped[int] = mapped_column(Integer)
    bloqueado_ate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # passive_deletes: a exclusão é feita pelo banco de forma otimizada
    logs: Mapped[list["LogAuditoria"]] = relationship(
        back_populates="usuario", passive_deletes=True)
    tentativas_login: Mapped[list["TentativaLogin"]
                             ] = relationship(back_populates="usuario", passive_deletes=True)
