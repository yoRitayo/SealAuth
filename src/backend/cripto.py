# CryptoService: AES-256-GCM (e-mail), HMAC-SHA256 (índice do e-mail) e RSA-PSS (assinatura).
# As chaves ficam fora do banco e do git, em keys/ (gere com scripts/gerar_chaves.py).
import hashlib
import hmac
import os
import unicodedata
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import LargeBinary
from sqlalchemy.types import TypeDecorator


def _diretorio_chaves() -> Path:
    # No container o docker-compose define CHAVES_DIR=/app/keys; localmente usa SealAuth/keys
    valor = os.getenv("CHAVES_DIR", "").strip()
    if valor:
        return Path(valor)
    return Path(__file__).resolve().parents[2] / "keys"


CHAVES_DIR = _diretorio_chaves()


def _ler_chave(nome: str) -> bytes:
    caminho = CHAVES_DIR / nome
    if not caminho.is_file():
        raise RuntimeError(
            f"Chave {caminho} não encontrada: rode scripts/gerar_chaves.py antes de subir a API"
        )
    return caminho.read_bytes()


_CHAVE_AES = _ler_chave("aes.key")
_CHAVE_HMAC = _ler_chave("hmac.key")
if len(_CHAVE_AES) != 32 or len(_CHAVE_HMAC) != 32:
    raise RuntimeError("aes.key e hmac.key precisam ter 32 bytes (256 bits)")

_privada = serialization.load_pem_private_key(
    _ler_chave("rsa_privada.pem"), password=None
)
_publica = serialization.load_pem_public_key(_ler_chave("rsa_publica.pem"))
if not isinstance(_privada, rsa.RSAPrivateKey) or not isinstance(
    _publica, rsa.RSAPublicKey
):
    raise RuntimeError("rsa_privada.pem e rsa_publica.pem precisam ser chaves RSA")
# Tipo declarado: o verificador de tipos sabe que são RSA também dentro das funções
CHAVE_PRIVADA: rsa.RSAPrivateKey = _privada
CHAVE_PUBLICA: rsa.RSAPublicKey = _publica


# ------- AES-256-GCM -------------
TAMANHO_NONCE = 12  # 96 bits, o recomendado para o GCM
# AAD: amarra o texto cifrado ao seu uso; um e-mail cifrado não serve em outro campo
_AAD_EMAIL = b"usuarios.email"


def cifrar(texto: str) -> bytes:
    # Nonce aleatório por cifragem: o mesmo e-mail gera bytes diferentes a cada vez
    nonce = os.urandom(TAMANHO_NONCE)
    return nonce + AESGCM(_CHAVE_AES).encrypt(nonce, texto.encode(), _AAD_EMAIL)


def decifrar(dados: bytes) -> str:
    # Levanta cryptography.exceptions.InvalidTag se o dado foi adulterado
    nonce, cifrado = dados[:TAMANHO_NONCE], dados[TAMANHO_NONCE:]
    return AESGCM(_CHAVE_AES).decrypt(nonce, cifrado, _AAD_EMAIL).decode()


def normalizar_email(email: str) -> str:
    return unicodedata.normalize("NFKC", email).strip().lower()


def indice_email(email: str) -> bytes:
    # Blind index: permite buscar pelo e-mail sem guardá-lo em claro nem decifrar a tabela
    return hmac.new(_CHAVE_HMAC, normalizar_email(email).encode(), hashlib.sha256).digest()


# ------- RSA-PSS -------------
_PSS = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)


def assinar(dados: bytes) -> bytes:
    return CHAVE_PRIVADA.sign(dados, _PSS, hashes.SHA256())


def verificar_assinatura(dados: bytes, assinatura: bytes) -> bool:
    try:
        CHAVE_PUBLICA.verify(assinatura, dados, _PSS, hashes.SHA256())
        return True
    except InvalidSignature:
        return False


# ------- TIPO DO SQLALCHEMY -------------
class EmailCifrado(TypeDecorator):
    """Coluna bytea que cifra ao gravar e decifra ao ler: o código lida só com str"""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else cifrar(value)

    def process_result_value(self, value, dialect):
        return None if value is None else decifrar(bytes(value))
