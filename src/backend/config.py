# Configurações lidas do ambiente (.env na raiz do projeto)
import os

from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRA_MINUTOS = int(os.getenv("JWT_EXPIRA_MINUTOS", "15"))

# Bloqueio automático após falhas de login consecutivas
LIMITE_FALHAS_LOGIN = 5
MINUTOS_BLOQUEIO_LOGIN = 15

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET não foi definido ainda. Configure no .env.")
