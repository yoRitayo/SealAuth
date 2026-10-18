# Configurações lidas do ambiente (.env na raiz do projeto)
import os

from dotenv import load_dotenv

load_dotenv()


def _carregar_jwt_secret() -> str:
    # Tenta um valor gerado pelo openssl
    caminho = os.getenv("JWT_SECRET_FILE", "/run/secrets/jwt_secret")
    if os.path.isfile(caminho):
        with open(caminho, encoding="utf-8") as arquivo:
            conteudo = arquivo.read().strip()
        if conteudo:
            return conteudo
    # Fallback para o valor do .env
    valor = os.getenv("JWT_SECRET", "").strip()
    if valor:
        return valor
    raise RuntimeError(
        "Nenhum segredo JWT encontrado: gere o docker secret ou defina JWT_SECRET no .env"
    )


JWT_SECRET = _carregar_jwt_secret()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRAMENTO_MINUTOS = int(os.getenv("JWT_EXPIRAMENTO_MINUTOS", "15"))
REFRESH_TOKEN_EXPIRAMENTO_DIAS = int(os.getenv("REFRESH_TOKEN_EXPIRAMENTO_DIAS", "1"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cookie Secure só funciona com HTTPS; em desenvolvimento local use COOKIE_SECURE=false
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"

# Bloqueio automático após falhas de login consecutivas
LIMITE_FALHAS_LOGIN = 5
MINUTOS_BLOQUEIO_LOGIN = 15

# Rate limiting do login
LIMITE_REQUISICOES_LOGIN = 7
JANELA_RATE_LIMIT_SEGUNDOS = 60

# Ambiente de execução: controla o fallback de e-mail (nunca logar tokens em produção)
AMBIENTE = os.getenv("ENV", "development").strip().lower()

# URL pública do frontend: usada no CORS e nos links enviados por e-mail
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3006")

# E-mail (ativação de conta e redefinição de senha)
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_SENHA = os.getenv("SMTP_SENHA", "")
SMTP_REMETENTE = os.getenv("SMTP_REMETENTE", "nao-responda@sealauth.local")

ATIVACAO_TOKEN_TTL_HORAS = int(os.getenv("ATIVACAO_TOKEN_TTL_HORAS", "24"))
REDEFINICAO_TOKEN_TTL_MINUTOS = int(os.getenv("REDEFINICAO_TOKEN_TTL_MINUTOS", "30"))
