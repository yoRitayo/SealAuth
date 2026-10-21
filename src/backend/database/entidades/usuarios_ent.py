from datetime import datetime
from uuid import UUID

from cripto import EmailCifrado
from database.database import Base
from sqlalchemy import DateTime, Integer, LargeBinary, Text, Uuid
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column


class Usuario(Base):
    """Tabela de usuários

    Args:
        Base: cria automaticamente um dicionário Python que armazena uma série de
        objetos Table chaveados para sua string nome.
    """

    __tablename__ = "USUARIOS"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    nome_usuario: Mapped[str] = mapped_column(CITEXT, unique=True)
    email: Mapped[str] = mapped_column(EmailCifrado)  # AES-256-GCM
    # HMAC-SHA256 do e-mail normalizado: busca sem decifrar (preenchido em auditoria.py)
    email_indice: Mapped[bytes | None] = mapped_column(LargeBinary, index=True)
    senha: Mapped[str] = mapped_column(Text)
    papel: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    falhas_consecutivas: Mapped[int] = mapped_column(Integer)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
