import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

BANCO_NOME = os.getenv("BANCO_NOME", "meubanco")


def _url_banco(usuario: str, senha: str, host: str, porta: int) -> URL:
    # URL.create evita problemas com caracteres especiais na senha (ex.: #, @, /)
    return URL.create(
        "postgresql+psycopg2",
        username=usuario,
        password=senha,
        host=host,
        port=porta,
        database=BANCO_NOME,
    )


# Usuário da aplicação (restrito), conectado pelo pgbouncer
engine = create_engine(_url_banco(
    usuario=os.getenv("APP_DB_USUARIO", "seal_app"),
    senha=os.getenv("APP_DB_SENHA", ""),
    host=os.getenv("APP_DB_HOST", "localhost"),
    porta=int(os.getenv("APP_DB_PORTA", "6432")),
), echo=True)

# Usuário admin (guardiao_app), direto no Postgres: só para criar tabelas e aplicar protecoes
engine_admin = create_engine(_url_banco(
    usuario=os.getenv("ADMIN_DB_USUARIO", "guardiao_app"),
    senha=os.getenv("ADMIN_DB_SENHA", ""),
    host=os.getenv("ADMIN_DB_HOST", "localhost"),
    porta=int(os.getenv("ADMIN_DB_PORTA", "5432")),
), echo=True)

# Fábrica de sessões
SessaoLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pylint pode reclamar mas deixa passar guys
# https://docs.sqlalchemy.org/en/21/changelog/whatsnew_20.html#whatsnew-20-orm-declarative-typing
class Base(DeclarativeBase):
    """Classe Base dinamicamente gerada e repassada como argumento na criação de tabelas em 
    modo declarativo no SQLAlchemy

    Args:
        DeclarativeBase: Classe que permite gerar a Base dinamicamente
    """
    pass

def obter_db():
    db = SessaoLocal()
    try:
        yield db # entrega para o fastapi
    finally:
        db.close() # entrega para o pgbouncer