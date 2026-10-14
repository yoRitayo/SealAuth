import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

CONTAINER_NOME=os.getenv("CONTAINER_NOME")
BANCO_NOME=os.getenv("BANCO_NOME")
BANCO_USUARIO=os.getenv("BANCO_USUARIO")
BANCO_SENHA=os.getenv("BANCO_SENHA")

URL_BANCO = f"postgresql+psycopg2://{BANCO_USUARIO}:{BANCO_SENHA}@{CONTAINER_NOME}/{BANCO_NOME}"

engine = create_engine(URL_BANCO, echo=True)

# Fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db # entrega para o fastapi
    finally:
        db.close() # entrega para o pgbouncer