# Gera chaves temporárias antes de importar os módulos do backend (cripto lê as chaves na importação)
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from scripts.gerar_chaves import gerar  # noqa: E402

_chaves = Path(tempfile.mkdtemp(prefix="sealauth-chaves-"))
gerar(_chaves, forcar=True)
os.environ["CHAVES_DIR"] = str(_chaves)
os.environ.setdefault("JWT_SECRET", "segredo-dos-testes")


@pytest.fixture
def dir_chaves() -> Path:
    # Diretório com as chaves válidas usadas pelos módulos importados nos testes
    return _chaves
