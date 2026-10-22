# Roda antes de importar o backend: o cripto já lê as chaves na
# importação, então as chaves temporárias precisam existir antes
import os
import sys
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
BACKEND = RAIZ / "src" / "backend"
sys.path.insert(0, str(BACKEND))

from scripts.gerar_chaves import gerar  # noqa: E402

_chaves = Path(tempfile.mkdtemp(prefix="sealauth-chaves-"))
gerar(_chaves, forcar=True)
os.environ["CHAVES_DIR"] = str(_chaves)
os.environ.setdefault("JWT_SECRET", "segredo-dos-testes")

# Redis e banco apontam para uma porta vazia: se algum teste escapar dos
# mocks, ele falha em vez de mexer em dados reais. O load_dotenv() não
# sobrescreve variáveis que já existem.
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
os.environ["APP_DB_HOST"] = "127.0.0.1"
os.environ["APP_DB_PORTA"] = "1"
os.environ["ADMIN_DB_HOST"] = "127.0.0.1"
os.environ["ADMIN_DB_PORTA"] = "1"


# Os testes E2E usam a API e o banco reais, então só rodam com SEALAUTH_E2E=1
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "e2e: exige a API em :8001 e grava no banco real"
    )


def pytest_collection_modifyitems(config, items):
    if os.getenv("SEALAUTH_E2E") == "1":
        return

    pular = pytest.mark.skip(
        reason="E2E: acessa a API e o banco reais (defina SEALAUTH_E2E=1)"
    )

    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(pular)
