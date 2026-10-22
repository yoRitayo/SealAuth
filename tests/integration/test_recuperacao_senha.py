
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import controllers.auth_con as auth_mod
import redis_cliente
from controllers.auth_con import AuthController
from database.database import obter_db


# =====================================================
# T09 - Token de recuperação expirado ou reutilizado
# =====================================================

NOVA_SENHA = "NovaSenha#Forte2026!"


class RedisSimulado:
    """Só o set/getdel do T09, com um relógio que dá para adiantar."""

    def __init__(self):
        self.dados = {}
        self.tempo = 0

    def set(self, chave, valor, ex=None):
        expiracao = self.tempo + ex if ex is not None else None
        self.dados[chave] = (valor, expiracao)
        return True

    def getdel(self, chave):
        # Remove a chave sempre; se já expirou, devolve None
        registro = self.dados.pop(chave, None)

        if registro is None:
            return None

        valor, expiracao = registro

        if expiracao is not None and self.tempo >= expiracao:
            return None

        return valor

    def avancar_tempo(self, segundos):
        self.tempo += segundos


@pytest.fixture
def ambiente_t09(monkeypatch):
    usuario = SimpleNamespace(
        id=uuid4(),
        senha="hash-antigo",
        falhas_consecutivas=2,
    )

    banco = MagicMock()
    banco.get.return_value = usuario

    # Troca o Redis real pelo simulado
    redis_falso = RedisSimulado()

    monkeypatch.setattr(
        redis_cliente,
        "cliente",
        redis_falso,
    )

    # Só o hash é simulado; o fluxo de redefinição é o real
    monkeypatch.setattr(
        auth_mod,
        "gerar_hash_senha",
        lambda senha: f"hash-simulado:{senha}",
    )

    # Não revoga sessões no Redis
    monkeypatch.setattr(
        auth_mod,
        "revogar_todas_sessoes",
        lambda usuario_id: None,
    )

    api = FastAPI()
    api.include_router(AuthController().router)

    api.dependency_overrides[obter_db] = lambda: banco

    with TestClient(api) as cliente:
        yield cliente, usuario, banco, redis_falso


def redefinir_senha(cliente, token):
    return cliente.post(
        "/auth/redefinir-senha",
        json={
            "token": token,
            "nova_senha": NOVA_SENHA,
        },
    )


# CENÁRIO 1 - Token válido funciona uma vez
def test_t09_token_valido_funciona(ambiente_t09):
    cliente, usuario, banco, redis_falso = ambiente_t09

    token = redis_cliente.criar_token_redefinicao(usuario.id)

    resposta = redefinir_senha(cliente, token)

    assert resposta.status_code == 200
    assert resposta.json() == {
        "detail": "Senha redefinida com sucesso"
    }

    assert usuario.senha == f"hash-simulado:{NOVA_SENHA}"
    assert usuario.falhas_consecutivas == 0

    banco.commit.assert_called_once()


# CENÁRIO 2 - Token reutilizado é recusado
def test_t09_token_reutilizado_rejeitado(ambiente_t09):
    cliente, usuario, banco, redis_falso = ambiente_t09

    token = redis_cliente.criar_token_redefinicao(usuario.id)

    primeira_resposta = redefinir_senha(cliente, token)
    segunda_resposta = redefinir_senha(cliente, token)

    assert primeira_resposta.status_code == 200

    assert segunda_resposta.status_code == 400, (
        "O token foi reutilizado, mas a API nao o rejeitou."
    )

    assert segunda_resposta.json() == {
        "detail": "Token de redefinição inválido ou expirado"
    }

    # Só a primeira chamada pode ter gravado a senha
    assert banco.commit.call_count == 1


# CENÁRIO 3 - Token expirado é recusado
def test_t09_token_expirado_rejeitado(ambiente_t09):
    cliente, usuario, banco, redis_falso = ambiente_t09

    token = redis_cliente.criar_token_redefinicao(usuario.id)

    # Passa 1 segundo do prazo configurado no backend
    prazo = redis_cliente.REDEFINICAO_TOKEN_TTL_MINUTOS * 60
    redis_falso.avancar_tempo(prazo + 1)

    resposta = redefinir_senha(cliente, token)

    assert resposta.status_code == 400, (
        "A API deveria rejeitar um token expirado."
    )

    assert resposta.json() == {
        "detail": "Token de redefinição inválido ou expirado"
    }

    # A senha continua a antiga
    assert usuario.senha == "hash-antigo"

    banco.commit.assert_not_called()


# CENÁRIO 4 - Token desconhecido é recusado
def test_t09_token_invalido_rejeitado(ambiente_t09):
    cliente, usuario, banco, redis_falso = ambiente_t09

    resposta = redefinir_senha(
        cliente,
        "token-inexistente-ficticio",
    )

    assert resposta.status_code == 400

    assert resposta.json() == {
        "detail": "Token de redefinição inválido ou expirado"
    }

    assert usuario.senha == "hash-antigo"

    banco.commit.assert_not_called()
