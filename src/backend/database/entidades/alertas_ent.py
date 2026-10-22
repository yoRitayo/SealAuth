from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from database.database import Base
from sqlalchemy import BigInteger, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from database.entidades.bloqueio_ip_ent import BloqueioIP


class Alerta(Base):
    """Tabela para guardar os logs de auditoria

    Args:
        Base: cria automaticamente um dicionário Python que armazena uma série de
        objetos Table chaveados para sua string nome.
    """

    __tablename__ = "ALERTAS"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Nulo em alerta só por IP (credential stuffing); excluir o usuário não apaga o alerta
    id_usuario: Mapped[UUID | None] = mapped_column(
        ForeignKey("USUARIOS.id", ondelete="SET NULL"), nullable=True
    )
    evento: Mapped[str] = mapped_column(Text)
    ip: Mapped[str] = mapped_column(INET)  # Armazena IPv4 ou IPv6
    jsonb: Mapped[dict[str, Any]] = mapped_column(JSONB)
    hash_anterior: Mapped[str] = mapped_column(Text)
    hash_atual: Mapped[str] = mapped_column(Text)
    assinatura: Mapped[bytes] = mapped_column(LargeBinary)  # RSA-PSS
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    bloqueio_ip: Mapped["BloqueioIP"] = relationship(back_populates="alerta")
