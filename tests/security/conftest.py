# Configuração dos testes E2E de segurança: endereço da API e checagem de que ela está no ar
import os
from urllib import error, request

import pytest

# Padrão do docker-compose; em outra máquina dá para apontar outro endereço com SEALAUTH_API_URL
API_PADRAO = "http://127.0.0.1:8001"


@pytest.fixture(scope="session")
def api_url():
    url = os.getenv("SEALAUTH_API_URL", API_PADRAO).rstrip("/")
    try:
        request.urlopen(f"{url}/docs", timeout=5)
    except error.HTTPError:
        pass  # respondeu com erro, mas a API está no ar
    except (error.URLError, OSError) as erro:
        # Pré-requisito do ambiente, não falha do sistema: aparece com o motivo em -rs
        pytest.skip(f"API indisponivel em {url} ({erro}). Suba a stack com 'make up'.")
    return url
