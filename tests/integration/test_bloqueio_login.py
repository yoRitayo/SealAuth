from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import controllers.auth_con as auth_mod
from controllers.auth_con import AuthController
from database.database import obter_db


# ============================================================
# T07 - Bloqueio da conta depois de cinco falhas de login
# ============================================================

SENHA_CORRETA = "SenhaCorreta#2026!"


@pytest.fixture
def ambiente_t07(monkeypatch):
    usuario = SimpleNamespace(
        id=uuid4(),
        senha="hash-simulado",
        papel="usuario",
        status="ativo",
        falhas_consecutivas=0,
        bloqueado_ate=None,
    )

    # A busca pelo nome sempre devolve esse usuário
    banco = MagicMock()
    banco.query.return_value.filter.return_value.first.return_value = usuario

    # Só a verificação da senha é simulada; a lógica de bloqueio é a do backend
    verificar_senha_mock = MagicMock(
        side_effect=lambda hash_senha, senha: senha == SENHA_CORRETA
    )

    monkeypatch.setattr(
        auth_mod, "verificar_senha", verificar_senha_mock
    )

    # Rate limit desligado para não interferir no bloqueio da conta
    monkeypatch.setattr(
        auth_mod, "verificar_rate_limit", lambda *args: True
    )

    # Sessão e tokens não importam neste teste
    monkeypatch.setattr(
        auth_mod, "revogar_todas_sessoes", lambda *args: None
    )

    monkeypatch.setattr(
        auth_mod,
        "criar_sessao",
        lambda *args, **kwargs: "refresh-ficticio",
    )

    monkeypatch.setattr(
        auth_mod, "criar_token_acesso", lambda *args: "jwt-ficticio"
    )

    # App só com as rotas reais de autenticação
    api = FastAPI()
    api.include_router(AuthController().router)

    api.dependency_overrides[obter_db] = lambda: banco

    with TestClient(api) as cliente:
        yield cliente, usuario, banco, verificar_senha_mock


def tentar_login(cliente, senha):
    return cliente.post(
        "/auth/login",
        data={
            "username": "usuario_teste",
            "password": senha,
        },
    )


# CENÁRIO 1 - Quatro falhas ainda não bloqueiam
def test_t07_quatro_falhas_nao_bloqueiam(ambiente_t07):
    cliente, usuario, banco, verificar_mock = ambiente_t07

    for tentativa in range(4):
        resposta = tentar_login(cliente, "SenhaErrada")

        assert resposta.status_code == 401, (
            f"Tentativa {tentativa + 1}: "
            f"esperado 401, recebido {resposta.status_code}"
        )

    assert usuario.falhas_consecutivas == 4
    assert usuario.status == "ativo"
    assert usuario.bloqueado_ate is None


# CENÁRIO 2 - A quinta falha bloqueia
def test_t07_quinta_falha_bloqueia(ambiente_t07):
    cliente, usuario, banco, verificar_mock = ambiente_t07

    for tentativa in range(5):
        resposta = tentar_login(cliente, "SenhaErrada")
        assert resposta.status_code == 401

    assert usuario.falhas_consecutivas == 5
    assert usuario.status == "bloqueado"
    assert usuario.bloqueado_ate is not None
    assert usuario.bloqueado_ate > datetime.now(UTC)


# CENÁRIO 3 - Sexta tentativa, mesmo com a senha certa, retorna 423
def test_t07_sexta_tentativa_retorna_423(ambiente_t07):
    cliente, usuario, banco, verificar_mock = ambiente_t07

    for tentativa in range(5):
        tentar_login(cliente, "SenhaErrada")

    resposta = tentar_login(cliente, SENHA_CORRETA)

    assert resposta.status_code == 423, (
        "A conta deveria continuar bloqueada. "
        f"HTTP recebido: {resposta.status_code}"
    )

    assert usuario.status == "bloqueado"

    # Com a conta bloqueada, a sexta senha nem chega a ser verificada
    assert verificar_mock.call_count == 5


# CENÁRIO 4 - Bloqueio manual (sem prazo) continua valendo
def test_t07_bloqueio_manual_permanece(ambiente_t07):
    cliente, usuario, banco, verificar_mock = ambiente_t07

    usuario.status = "bloqueado"
    usuario.bloqueado_ate = None

    resposta = tentar_login(cliente, SENHA_CORRETA)

    assert resposta.status_code == 423
    assert usuario.status == "bloqueado"
    verificar_mock.assert_not_called()


# CENÁRIO 5 - Depois que o bloqueio expira, a senha certa entra
def test_t07_bloqueio_expirado(ambiente_t07):
    cliente, usuario, banco, verificar_mock = ambiente_t07

    usuario.status = "bloqueado"
    usuario.falhas_consecutivas = 5
    usuario.bloqueado_ate = datetime.now(UTC) - timedelta(seconds=1)

    resposta = tentar_login(cliente, SENHA_CORRETA)

    assert resposta.status_code == 200
    assert usuario.status == "ativo"
    assert usuario.falhas_consecutivas == 0
    assert usuario.bloqueado_ate is None
