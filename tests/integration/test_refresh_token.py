
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import fakeredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import controllers.auth_con as auth_mod
import redis_cliente
from controllers.auth_con import AuthController
from database.database import obter_db


# =====================================================
# T10 - Reusar o refresh token revoga a família inteira
# =====================================================


@pytest.fixture
def ambiente_t10(monkeypatch):
    usuario = SimpleNamespace(
        id=uuid4(),
        papel="usuario",
        status="ativo",
    )

    banco = MagicMock()
    banco.get.return_value = usuario

    familia = str(uuid4())

    # Redis em memória no lugar do real. O script Lua de rotação é
    # registrado no cliente real na importação, então precisa ser refeito aqui.
    redis_falso = fakeredis.FakeRedis(decode_responses=True)

    monkeypatch.setattr(redis_cliente, "cliente", redis_falso)

    monkeypatch.setattr(
        redis_cliente,
        "_ROTACIONAR",
        redis_falso.register_script(redis_cliente._ROTACIONAR.script),
    )

    # Só a emissão do JWT é simulada
    monkeypatch.setattr(
        auth_mod,
        "criar_token_acesso",
        lambda *args: "jwt-ficticio",
    )

    api = FastAPI()
    api.include_router(AuthController().router)
    api.dependency_overrides[obter_db] = lambda: banco

    token_inicial = redis_cliente.criar_sessao(
        usuario.id,
        familia=familia,
    )

    # Base https para o TestClient aceitar cookie Secure
    with TestClient(
        api,
        base_url="https://testserver",
    ) as cliente:
        yield cliente, usuario, familia, token_inicial


def renovar(cliente, token=None):
    if token is None:
        return cliente.post(
            "/auth/refresh",
        )

    return cliente.post(
        "/auth/refresh",
        headers={"Cookie": f"refresh_token={token}"},
    )


# CENÁRIO 1 - Token válido gera um refresh token novo
def test_t10_token_valido_rotaciona(ambiente_t10):
    cliente, usuario, familia, token = ambiente_t10

    resposta = renovar(cliente, token)

    assert resposta.status_code == 200
    assert resposta.json()["access_token"] == "jwt-ficticio"

    novo_token = resposta.cookies.get("refresh_token")

    assert novo_token is not None
    assert novo_token != token


# CENÁRIO 2 - Reuso derruba a família inteira
def test_t10_reuso_revoga_familia(ambiente_t10):
    cliente, usuario, familia, token = ambiente_t10

    # Primeiro uso: normal
    primeira = renovar(cliente, token)
    assert primeira.status_code == 200

    novo_token = primeira.cookies.get("refresh_token")
    assert novo_token is not None

    # O token antigo de novo: é reuso
    segunda = renovar(cliente, token)

    assert segunda.status_code == 401, (
        "O refresh token reutilizado deveria ser rejeitado."
    )

    assert redis_cliente.cliente.exists(
        f"familia_revogada:{familia}"
    ) == 1

    # O token novo, da mesma família, também deixa de valer
    terceira = renovar(cliente, novo_token)

    assert terceira.status_code == 401, (
        "O reuso do token antigo deveria invalidar "
        "tambem o token novo da mesma familia."
    )


# CENÁRIO 3 - Família já revogada
def test_t10_familia_revogada(ambiente_t10):
    cliente, usuario, familia, token = ambiente_t10

    redis_cliente.revogar_familia(familia)

    resposta = renovar(cliente, token)

    assert resposta.status_code == 401


# CENÁRIO 4 - Token desconhecido
def test_t10_token_desconhecido(ambiente_t10):
    cliente, usuario, familia, token = ambiente_t10

    token_invalido = f"inexistente-{uuid4().hex}"

    resposta = renovar(cliente, token_invalido)

    assert resposta.status_code == 401


# CENÁRIO 5 - Refresh sem cookie
def test_t10_sem_cookie(ambiente_t10):
    cliente, usuario, familia, token = ambiente_t10

    resposta = renovar(cliente)

    assert resposta.status_code == 401
