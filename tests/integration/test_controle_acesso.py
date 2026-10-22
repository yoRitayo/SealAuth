
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controllers.usuarios_con import UsuariosController
from database.database import obter_db
from seguranca import verificar_usuario


# =====================================================
# T11 - Controle de acesso por papel (RBAC)
#
# Critério: quem não tem permissão recebe 403 na rota de admin
#
# O cenário 5 (auditoria do 403) está em
# tests/pendentes/pendente_t11_auditoria_acesso_negado.py,
# aguardando confirmação de requisito.
# =====================================================


@pytest.fixture
def criar_cliente_t11():

    @contextmanager
    def preparar(papel):
        usuario = SimpleNamespace(
            id=uuid4(),
            papel=papel,
        )

        banco = MagicMock()

        # Lista vazia para quando o acesso é liberado
        banco.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        api = FastAPI()
        api.include_router(UsuariosController().router)

        # Só a identificação do usuário é simulada; o ChecadorPermissao é o real
        api.dependency_overrides[verificar_usuario] = lambda: usuario
        api.dependency_overrides[obter_db] = lambda: banco

        with TestClient(api) as cliente:
            yield cliente, banco

    return preparar


# CENÁRIOS 1, 2 e 3 - Papéis sem permissão
@pytest.mark.parametrize(
    "papel",
    ["usuario", "analista", "desconhecido"],
)
def test_t11_acesso_sem_permissao_retorna_403(
    criar_cliente_t11, papel
):
    with criar_cliente_t11(papel) as (cliente, banco):

        resposta = cliente.get("/usuarios")

        assert resposta.status_code == 403, (
            f"O papel {papel} nao deveria acessar "
            f"a rota administrativa. "
            f"HTTP recebido: {resposta.status_code}"
        )

        assert resposta.json() == {
            "detail": "Você não tem permissão para acessar este recurso."
        }

        # O 403 tem que vir antes de qualquer consulta ao banco
        banco.query.assert_not_called()


# CENÁRIO 4 - Admin consegue acessar
def test_t11_admin_consegue_acessar(criar_cliente_t11):
    with criar_cliente_t11("admin") as (cliente, banco):

        resposta = cliente.get("/usuarios")

        assert resposta.status_code == 200
        assert resposta.json() == []

        banco.query.assert_called_once()
