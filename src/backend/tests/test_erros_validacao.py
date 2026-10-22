# Testes do handler de 422 (erros_validacao.py): nenhum dado enviado volta na resposta
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from controllers.auth_con import AuthController
from controllers.usuarios_con import UsuariosController
from database.database import obter_db
from erros_validacao import CAMPOS_DO_ERRO, validacao_sem_dados_enviados
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from seguranca import verificar_usuario

SENHA_FORTE = "Secreta#Forte2026!"
SENHA_ATUAL = "Atual#Secreta2026!"
SENHA_FRACA = "fraca123"
TOKEN = "token-de-redefinicao-secreto"
ADMIN = SimpleNamespace(id=uuid4(), papel="admin", status="ativo")
MSG_POLITICA = (
    "A senha deve ter no mínimo 8 caracteres, com letras maiúscula/minúscula, "
    "1 dígito e ao menos um símbolo especial"
)


def _cliente(com_handler: bool = True) -> TestClient:
    # Mesmo registro do main.py; o banco é falso porque o 422 sai antes de qualquer consulta
    handlers = {RequestValidationError: validacao_sem_dados_enviados} if com_handler else {}
    api = FastAPI(exception_handlers=handlers)
    api.include_router(UsuariosController().router)
    api.include_router(AuthController().router)
    api.dependency_overrides[obter_db] = lambda: MagicMock()
    api.dependency_overrides[verificar_usuario] = lambda: ADMIN
    return TestClient(api)


# ------- NENHUM DADO ENVIADO NA RESPOSTA -------------
@pytest.mark.parametrize(
    ("metodo", "caminho", "dados", "segredos"),
    [
        pytest.param("post", "/usuarios", {"json": {"nome_usuario": "ana", "email": "a@x.com", "senha": SENHA_FRACA}},
                     [SENHA_FRACA], id="cadastro-senha-fraca"),
        pytest.param("post", "/usuarios", {"json": {"nome_usuario": "ana", "senha": SENHA_FORTE}},
                     [SENHA_FORTE], id="cadastro-sem-email"),
        pytest.param("patch", f"/usuarios/{ADMIN.id}/senha", {"json": {"senha_atual": SENHA_ATUAL, "nova_senha": SENHA_FRACA}},
                     [SENHA_ATUAL, SENHA_FRACA], id="alteracao-senha-fraca"),
        pytest.param("patch", f"/usuarios/{ADMIN.id}/senha", {"json": {"senha_atual": SENHA_ATUAL}},
                     [SENHA_ATUAL], id="alteracao-sem-nova-senha"),
        pytest.param("post", "/auth/redefinir-senha", {"json": {"token": TOKEN, "nova_senha": SENHA_FRACA}},
                     [TOKEN, SENHA_FRACA], id="redefinicao-senha-fraca"),
        pytest.param("post", "/auth/redefinir-senha", {"json": {"token": TOKEN}},
                     [TOKEN], id="redefinicao-sem-nova-senha"),
        pytest.param("post", "/auth/login", {"data": {"password": SENHA_FORTE}},
                     [SENHA_FORTE], id="login-sem-usuario"),
        pytest.param("post", "/auth/login", {"data": {"username": "ana", "password": SENHA_FORTE, "grant_type": "errado"}},
                     [SENHA_FORTE, "errado"], id="login-grant-type-invalido"),
    ],
)
def test_422_nao_devolve_dados_enviados(metodo, caminho, dados, segredos):
    resposta = getattr(_cliente(), metodo)(caminho, **dados)
    assert resposta.status_code == 422
    for segredo in segredos:
        assert segredo not in resposta.text
    for erro in resposta.json()["detail"]:
        assert set(erro) <= set(CAMPOS_DO_ERRO) and {"loc", "msg"} <= set(erro)


def test_sem_o_handler_o_fastapi_expoe_a_senha():
    # Controle: mostra o problema que o handler resolve (o corpo inteiro volta no "input")
    resposta = _cliente(com_handler=False).post("/usuarios", json={"nome_usuario": "ana", "senha": SENHA_FORTE})
    assert resposta.status_code == 422
    assert SENHA_FORTE in resposta.text


# ------- OS OUTROS ERROS CONTINUAM IGUAIS -------------
def test_mensagem_da_politica_de_senha_continua():
    resposta = _cliente().post("/usuarios", json={"nome_usuario": "ana", "email": "a@x.com", "senha": "123"})
    assert resposta.json() == {"detail": [{"type": "senha_fraca", "loc": ["body", "senha"], "msg": MSG_POLITICA}]}


@pytest.mark.parametrize(
    ("metodo", "caminho", "dados", "tipo", "inicio_loc"),
    [
        pytest.param("patch", f"/usuarios/{ADMIN.id}/papel", {"json": {"papel": "superadmin"}},
                     "literal_error", ["body", "papel"], id="papel-invalido"),
        pytest.param("get", "/usuarios", {"params": {"pulo": "abc"}}, "int_parsing", ["query", "pulo"], id="query-invalida"),
        pytest.param("get", "/usuarios/nao-e-uuid", {}, "uuid_parsing", ["path", "id_usuario"], id="path-invalido"),
        pytest.param("post", "/usuarios", {"content": b"{nao e json", "headers": {"Content-Type": "application/json"}},
                     "json_invalid", ["body"], id="json-malformado"),
    ],
)
def test_outros_erros_mantem_type_loc_e_msg(metodo, caminho, dados, tipo, inicio_loc):
    resposta = getattr(_cliente(), metodo)(caminho, **dados)
    assert resposta.status_code == 422
    (erro,) = resposta.json()["detail"]
    assert erro["type"] == tipo
    assert erro["loc"][: len(inicio_loc)] == inicio_loc
    assert erro["msg"]
