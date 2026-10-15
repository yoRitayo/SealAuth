from datetime import datetime

from database import Base
from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.orm import Mapped, mapped_column


class Alertas(Base):
    """Tabela para guardar os logs de auditoria

    Args:
        Base: cria automaticamente um dicionário Python que armazena uma série de 
        objetos Table chaveados para sua string nome. 
    """

    __tablename__ = "BLOQUEIOS_IP"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_alerta: Mapped[int] = mapped_column(ForeignKey("alertas.id", ondelete="CASCADE"))
    faixa : Mapped[str] = mapped_column(CIDR) # armazena endereço de sub-rede
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))