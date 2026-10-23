
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import controllers.auth_con as auth_mod
from controllers.auth_con import AuthController
from database.database import obter_db


# ====================================================
# T12 - Cookies HttpOnly, Secure e SameSite=Strict
# ====================================================

SENHA_CORRETA = "SenhaCorreta#2026!"


@pytest.fixture
def ambiente_t12(monkeypatch):
    usuario = SimpleNamespace(
        id=uuid4(),
        senha="hash-ficticio",
        papel="usuario",
        status="ativo",
        falhas_consecutivas=0,
        bloqueado_ate=None,
    )

    banco = MagicMock()

    banco.query.return_value.filter.return_value.first.return_value = usuario
    banco.get.return_value = usuario

    # Liga o cookie Secure como em produção, só durante o teste
    monkeypatch.setattr(auth_mod, "COOKIE_SECURE", True)

    monkeypatch.setattr(
        auth_mod,
        "verificar_rate_limit",
        lambda *args: True,
    )

    monkeypatch.setattr(
        auth_mod,
        "verificar_senha",
        lambda hash_senha, senha: senha == SENHA_CORRETA,
    )

    monkeypatch.setattr(
        auth_mod,
        "revogar_todas_sessoes",
        lambda *args: None,
    )

    monkeypatch.setattr(
        auth_mod,
        "criar_sessao",
        lambda *args, **kwargs: "refresh-ficticio",
    )

    monkeypatch.setattr(
        auth_mod,
        "criar_token_acesso",
        lambda *args: "jwt-ficticio",
    )

    rotacionar_mock = MagicMock(
        return_value=(
            "ok",
            "familia-ficticia",
            str(usuario.id),
            "refresh-renovado",
        )
    )

    revogar_mock = MagicMock()

    monkeypatch.setattr(
        auth_mod,
        "rotacionar_sessao",
        rotacionar_mock,
    )

    monkeypatch.setattr(
        auth_mod,
        "revogar_sessao",
        revogar_mock,
    )

    api = FastAPI()
    api.include_router(AuthController().router)

    api.dependency_overrides[obter_db] = lambda: banco

    # Base https para o TestClient aceitar cookie Secure
    with TestClient(
        api,
        base_url="https://testserver",
    ) as cliente:
        yield cliente, rotacionar_mock, revogar_mock


def verificar_atributos_seguros(resposta):
    cookie = resposta.headers.get("set-cookie", "")

    assert cookie, "Nenhum cookie foi enviado."

    atributos = [
        parte.strip().lower()
        for parte in cookie.split(";")
    ]

    assert atributos[0].startswith("refresh_token=")
    assert "httponly" in atributos
    assert "secure" in atributos
    assert "samesite=strict" in atributos
    assert "path=/auth" in atributos


# CENÁRIO 1 - Login gera cookie seguro
def test_t12_login_cookie_seguro(ambiente_t12):
    cliente, _, _ = ambiente_t12

    resposta = cliente.post(
        "/auth/login",
        data={
            "username": "usuario_ficticio",
            "password": SENHA_CORRETA,
        },
    )

    assert resposta.status_code == 200
    verificar_atributos_seguros(resposta)


# CENÁRIO 2 - Refresh gera cookie seguro com o token novo
def test_t12_refresh_cookie_seguro(ambiente_t12):
    cliente, rotacionar_mock, _ = ambiente_t12

    resposta = cliente.post(
        "/auth/refresh",
        headers={
            "Cookie": "refresh_token=refresh-original",
        },
    )

    assert resposta.status_code == 200
    verificar_atributos_seguros(resposta)

    rotacionar_mock.assert_called_once_with(
        "refresh-original"
    )

    cookie = resposta.headers["set-cookie"]

    assert "refresh_token=refresh-renovado" in cookie


# CENÁRIO 3 - Logout apaga o cookie (max-age=0)
def test_t12_logout_remove_cookie(ambiente_t12):
    cliente, _, revogar_mock = ambiente_t12

    resposta = cliente.post(
        "/auth/logout",
        headers={
            "Cookie": "refresh_token=refresh-ficticio",
        },
    )

    assert resposta.status_code == 204

    revogar_mock.assert_called_once_with(
        "refresh-ficticio"
    )

    verificar_atributos_seguros(resposta)

    cookie = resposta.headers["set-cookie"].lower()

    assert "max-age=0" in cookie


# CENÁRIO 4 - Login inválido não gera cookie
def test_t12_login_invalido_sem_cookie(ambiente_t12):
    cliente, _, _ = ambiente_t12

    resposta = cliente.post(
        "/auth/login",
        data={
            "username": "usuario_ficticio",
            "password": "SenhaErrada",
        },
    )

    assert resposta.status_code == 401

    assert "refresh_token=" not in resposta.headers.get(
        "set-cookie", ""
    )
