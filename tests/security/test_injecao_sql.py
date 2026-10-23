from urllib import request, parse, error

import pytest

# Precisa da API no ar (SEALAUTH_API_URL, padrão :8001) e grava a tentativa no banco dela
pytestmark = pytest.mark.e2e


def test_login_rejeita_injecao_sql(api_url):
    # Payload clássico de SQL injection no campo de usuário
    dados = parse.urlencode({
        "username": "' OR '1'='1' --",
        "password": "SenhaFicticia#123",
    }).encode()

    requisicao = request.Request(
        f"{api_url}/auth/login",
        data=dados,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST",
    )

    try:
        with request.urlopen(requisicao, timeout=10) as resposta:
            status = resposta.status
    except error.HTTPError as excecao:
        status = excecao.code

    # 429 é o rate limit (7 tentativas por minuto), não o resultado do teste
    dica = " (rate limit: aguarde 1 minuto e rode de novo)" if status == 429 else ""
    assert status == 401, (
        f"Esperado HTTP 401, mas recebido HTTP {status}{dica}"
    )
