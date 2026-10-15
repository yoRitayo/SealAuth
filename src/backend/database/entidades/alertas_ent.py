import uuid
from datetime import datetime
from typing import Any, Dict

from bloqueio_ip_ent import BloqueioIP
from database import Base
from sqlalchemy import BigInteger, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Alerta(Base):
    """Tabela para guardar os logs de auditoria

    Args:
        Base: cria automaticamente um dicionário Python que armazena uma série de 
        objetos Table chaveados para sua string nome. 
    """

    __tablename__ = "logs_auditoria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    evento : Mapped[str] = mapped_column(Text)
    ip: Mapped[str] = mapped_column(INET) # Armazena IPv4 ou IPv6 
    jsonb: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    hash_anterior: Mapped[str] = mapped_column(Text)
    hash_atual: Mapped[str] = mapped_column(Text)
    assinatura: Mapped[str] = mapped_column(LargeBinary)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    bloqueio_ip: Mapped[BloqueioIP] = relationship(back_populates="alerta")
