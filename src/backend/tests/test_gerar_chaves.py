# Testes do gerador de chaves (scripts/gerar_chaves.py)
import ipaddress
import os
import sys
from datetime import timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from scripts import gerar_chaves

ARQUIVOS = ["aes.key", "hmac.key", "rsa_privada.pem", "rsa_publica.pem", "cert.key", "cert.pem"]


@pytest.fixture
def chaves(tmp_path):
    destino = tmp_path / "keys"
    gerar_chaves.gerar(destino, forcar=False)
    return destino


def _privada(caminho):
    return serialization.load_pem_private_key(caminho.read_bytes(), password=None)


# ------- _pem_privada / _certificado -------------
def test_pem_privada_e_pkcs8_sem_senha():
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = gerar_chaves._pem_privada(chave)
    assert pem.startswith(b"-----BEGIN PRIVATE KEY-----")
    carregada = serialization.load_pem_private_key(pem, password=None)
    assert carregada.private_numbers() == chave.private_numbers()


def test_certificado_autoassinado_para_localhost():
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    certificado = x509.load_pem_x509_certificate(gerar_chaves._certificado(chave))
    cn = certificado.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    assert cn == "localhost"
    assert certificado.issuer == certificado.subject
    assert certificado.public_key().public_numbers() == chave.public_key().public_numbers()
    certificado.public_key().verify(
        certificado.signature,
        certificado.tbs_certificate_bytes,
        padding.PKCS1v15(),
        certificado.signature_hash_algorithm,
    )


def test_certificado_san_e_validade():
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    certificado = x509.load_pem_x509_certificate(gerar_chaves._certificado(chave))
    san = certificado.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert san.get_values_for_type(x509.DNSName) == ["localhost"]
    assert san.get_values_for_type(x509.IPAddress) == [ipaddress.ip_address("127.0.0.1")]
    assert certificado.not_valid_after_utc - certificado.not_valid_before_utc == timedelta(days=365)
    assert isinstance(certificado.signature_hash_algorithm, hashes.SHA256)


# ------- gerar -------------
def test_destino_padrao_e_keys_na_raiz():
    assert gerar_chaves.DESTINO_PADRAO.name == "keys"
    assert (gerar_chaves.DESTINO_PADRAO.parent / "src" / "backend").is_dir()


def test_gerar_cria_todos_os_arquivos(chaves):
    assert sorted(p.name for p in chaves.iterdir()) == sorted(ARQUIVOS)


def test_gerar_cria_diretorios_intermediarios(tmp_path):
    destino = tmp_path / "a" / "b" / "keys"
    gerar_chaves.gerar(destino, forcar=False)
    assert (destino / "aes.key").is_file()


def test_chaves_simetricas_de_256_bits(chaves):
    aes, chave_hmac = (chaves / "aes.key").read_bytes(), (chaves / "hmac.key").read_bytes()
    assert len(aes) == 32 and len(chave_hmac) == 32
    assert aes != chave_hmac


def test_par_rsa_3072_coerente(chaves):
    privada = _privada(chaves / "rsa_privada.pem")
    publica = serialization.load_pem_public_key((chaves / "rsa_publica.pem").read_bytes())
    assert isinstance(privada, rsa.RSAPrivateKey)
    assert privada.key_size == 3072
    assert privada.public_key().public_numbers() == publica.public_numbers()


def test_certificado_usa_chave_propria(chaves):
    certificado = x509.load_pem_x509_certificate((chaves / "cert.pem").read_bytes())
    chave_tls = _privada(chaves / "cert.key")
    assert certificado.public_key().public_numbers() == chave_tls.public_key().public_numbers()
    # A chave do TLS é separada da chave que assina JWT e logs
    assert chave_tls.private_numbers() != _privada(chaves / "rsa_privada.pem").private_numbers()


def test_gerar_nao_sobrescreve_sem_forcar(chaves, capsys):
    antes = {nome: (chaves / nome).read_bytes() for nome in ARQUIVOS}
    capsys.readouterr()
    gerar_chaves.gerar(chaves, forcar=False)
    assert "já existem" in capsys.readouterr().out
    assert {nome: (chaves / nome).read_bytes() for nome in ARQUIVOS} == antes


def test_gerar_com_forcar_troca_as_chaves(chaves):
    aes_antes = (chaves / "aes.key").read_bytes()
    privada_antes = (chaves / "rsa_privada.pem").read_bytes()
    gerar_chaves.gerar(chaves, forcar=True)
    assert (chaves / "aes.key").read_bytes() != aes_antes
    assert (chaves / "rsa_privada.pem").read_bytes() != privada_antes


def test_gerar_lista_os_arquivos_criados(tmp_path, capsys):
    gerar_chaves.gerar(tmp_path / "keys", forcar=False)
    saida = capsys.readouterr().out
    assert all(nome in saida for nome in ARQUIVOS)


@pytest.mark.skipif(sys.platform == "win32", reason="permissões POSIX não se aplicam no Windows")
def test_chaves_privadas_so_para_o_dono(chaves):
    for nome in ["aes.key", "hmac.key", "rsa_privada.pem", "cert.key"]:
        assert os.stat(chaves / nome).st_mode & 0o777 == 0o600
