# Testes do JWT RS256 e do registro do ator (seguranca.py)
import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import cripto
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from database import entidades
from fastapi import HTTPException
from seguranca import JWT_ALGORITHM, criar_token_acesso, decodificar_token, verificar_usuario


def _b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def _payload(token: str) -> dict:
    corpo = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(corpo + "=" * (-len(corpo) % 4)))


def _usuario(status: str = "ativo") -> entidades.Usuario:
    return entidades.Usuario(
        id=uuid4(),
        nome_usuario="ana",
        email="ana@exemplo.com",
        senha="hash",
        papel="usuario",
        status=status,
        falhas_consecutivas=0,
        criado_em=datetime.now(UTC),
    )


class _DbFalso:
    def __init__(self, usuario=None):
        self.usuario = usuario
        self.info = {}

    def get(self, modelo, id_):
        return self.usuario if self.usuario is not None and self.usuario.id == id_ else None


# ------- criar_token_acesso -------------
def test_algoritmo_e_rs256():
    assert JWT_ALGORITHM == "RS256"
    assert jwt.get_unverified_header(criar_token_acesso(uuid4()))["alg"] == "RS256"


def test_token_traz_claims_do_documento():
    usuario_id = uuid4()
    payload = _payload(criar_token_acesso(usuario_id, "analista"))
    assert payload["sub"] == str(usuario_id)
    assert payload["papel"] == "analista"
    assert payload["type"] == "access"
    assert payload["exp"] - payload["iat"] == 15 * 60


def test_papel_e_opcional():
    assert _payload(criar_token_acesso(uuid4()))["papel"] is None


def test_token_assinado_pela_chave_privada():
    token = criar_token_acesso(uuid4(), "usuario")
    jwt.decode(token, cripto.CHAVE_PUBLICA, algorithms=["RS256"])  # não levanta


# ------- decodificar_token -------------
def test_decodificar_token_valido():
    usuario_id = uuid4()
    payload = decodificar_token(criar_token_acesso(usuario_id, "usuario"))
    assert payload["sub"] == str(usuario_id)


def test_decodificar_recusa_papel_alterado():
    cabecalho, corpo, assinatura = criar_token_acesso(uuid4(), "usuario").split(".")
    payload = _payload(f"{cabecalho}.{corpo}.{assinatura}")
    payload["papel"] = "admin"
    forjado = f"{cabecalho}.{_b64(json.dumps(payload).encode())}.{assinatura}"
    with pytest.raises(jwt.InvalidSignatureError):
        decodificar_token(forjado)


def test_decodificar_recusa_outra_chave_rsa():
    outra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode({"sub": str(uuid4()), "type": "access"}, outra, algorithm="RS256")
    with pytest.raises(jwt.InvalidSignatureError):
        decodificar_token(token)


def test_decodificar_recusa_troca_para_hs256():
    # Ataque clássico: assinar com HMAC usando a chave pública como segredo
    publica_pem = cripto.CHAVE_PUBLICA.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    cabecalho = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    corpo = _b64(json.dumps({"sub": str(uuid4()), "type": "access", "papel": "admin"}).encode())
    assinatura = _b64(hmac.new(publica_pem, f"{cabecalho}.{corpo}".encode(), hashlib.sha256).digest())
    with pytest.raises(jwt.InvalidTokenError):
        decodificar_token(f"{cabecalho}.{corpo}.{assinatura}")


def test_decodificar_recusa_alg_none():
    token = jwt.encode({"sub": str(uuid4()), "type": "access"}, None, algorithm="none")
    with pytest.raises(jwt.InvalidTokenError):
        decodificar_token(token)


def test_decodificar_recusa_token_expirado():
    agora = datetime.now(UTC)
    token = jwt.encode(
        {"sub": str(uuid4()), "iat": agora - timedelta(minutes=30), "exp": agora - timedelta(minutes=15)},
        cripto.CHAVE_PRIVADA,
        algorithm="RS256",
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decodificar_token(token)


# ------- verificar_usuario -------------
def test_verificar_usuario_devolve_usuario_e_registra_ator():
    usuario = _usuario()
    db = _DbFalso(usuario)
    assert verificar_usuario(criar_token_acesso(usuario.id, "usuario"), db) is usuario
    assert db.info["ator_id"] == usuario.id


def test_verificar_usuario_token_invalido():
    db = _DbFalso(_usuario())
    with pytest.raises(HTTPException) as erro:
        verificar_usuario("nao.e.jwt", db)
    assert erro.value.status_code == 401
    assert "ator_id" not in db.info


def test_verificar_usuario_inexistente():
    db = _DbFalso(None)
    with pytest.raises(HTTPException) as erro:
        verificar_usuario(criar_token_acesso(uuid4()), db)
    assert erro.value.status_code == 401


def test_verificar_usuario_recusa_token_que_nao_e_de_acesso():
    usuario = _usuario()
    token = jwt.encode(
        {"sub": str(usuario.id), "type": "refresh", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        cripto.CHAVE_PRIVADA,
        algorithm="RS256",
    )
    with pytest.raises(HTTPException) as erro:
        verificar_usuario(token, _DbFalso(usuario))
    assert erro.value.status_code == 401


def test_verificar_usuario_bloqueado_nao_vira_ator():
    usuario = _usuario(status="bloqueado")
    db = _DbFalso(usuario)
    with pytest.raises(HTTPException) as erro:
        verificar_usuario(criar_token_acesso(usuario.id), db)
    assert erro.value.status_code == 403
    assert "ator_id" not in db.info
