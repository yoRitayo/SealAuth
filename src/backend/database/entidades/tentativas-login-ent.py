import uuid
from datetime import datetime

from database import Base
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import CITEXT, INET
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TentativasLogin(Base):
    """Tabela para guardar as tentativas de login

    Args:
        Base: cria automaticamente um dicionário Python que armazena uma série de 
        objetos Table chaveados para sua string nome. 
    """

    __tablename__ = "TENTATIVAS_LOGIN"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    nome_usuario_informado: Mapped[str] = mapped_column(CITEXT)
    ip: Mapped[str] = mapped_column(INET) # Armazena IPv4 ou IPv6 
    com_sucesso: Mapped[bool] = mapped_column(Boolean, default=True)
    motivo: Mapped[str] = mapped_column(Text)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now)