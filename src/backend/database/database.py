import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

CONTAINER_NOME=os.getenv("CONTAINER_NOME", "meu_postgres_container")
BANCO_NOME=os.getenv("BANCO_NOME", "meubanco")
BANCO_USUARIO=os.getenv("BANCO_USUARIO", "meusuario")
BANCO_SENHA=os.getenv("BANCO_SENHA", "uma_senha_muito_segura_e_longa")

URL_BANCO = f"postgresql+psycopg2://{BANCO_USUARIO}:{BANCO_SENHA}@{CONTAINER_NOME}/{BANCO_NOME}"

engine = create_engine(URL_BANCO, echo=True)

# Fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pylint pode reclamar mas deixa passar guys
# https://docs.sqlalchemy.org/en/21/changelog/whatsnew_20.html#whatsnew-20-orm-declarative-typing
class Base(DeclarativeBase):
    """Classe Base dinamicamente gerada e repassada como argumento na criação de tabelas em 
    modo declarativo no SQLAlchemy

    Args:
        DeclarativeBase: Classe que permite gerar a Base dinamicamente
    """
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db # entrega para o fastapi
    finally:
        db.close() # entrega para o pgbouncer