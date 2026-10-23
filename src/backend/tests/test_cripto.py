# Testes do CryptoService (cripto.py)
import hashlib
import hmac
import importlib.util
import shutil
from pathlib import Path

import cripto
import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from database import entidades
from sqlalchemy import LargeBinary


def _importar_cripto_isolado(monkeypatch, diretorio: Path):
    # Executa cripto.py como um módulo novo, para testar a validação feita na importação
    monkeypatch.setenv("CHAVES_DIR", str(diretorio))
    spec = importlib.util.spec_from_file_location("cripto_isolado", cripto.__file__)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _copiar_chaves(origem: Path, destino: Path) -> Path:
    shutil.copytree(origem, destino)
    return destino


# ------- CARGA DAS CHAVES -------------
def test_diretorio_chaves_usa_variavel_de_ambiente(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAVES_DIR", str(tmp_path))
    assert cripto._diretorio_chaves() == tmp_path


def test_diretorio_chaves_sem_variavel_usa_keys_na_raiz(monkeypatch):
    monkeypatch.delenv("CHAVES_DIR", raising=False)
    caminho = cripto._diretorio_chaves()
    assert caminho.name == "keys"
    # No container, CHAVES_DIR aponta para /app/keys; localmente para SealAuth/keys
    pai = caminho.parent
    assert (pai / "src" / "backend" / "cripto.py").is_file() or (pai / "cripto.py").is_file()


def test_diretorio_chaves_ignora_valor_em_branco(monkeypatch):
    monkeypatch.setenv("CHAVES_DIR", "   ")
    assert cripto._diretorio_chaves().name == "keys"


def test_ler_chave_devolve_bytes_do_arquivo(monkeypatch, tmp_path):
    (tmp_path / "teste.key").write_bytes(b"\x00\x01\x02")
    monkeypatch.setattr(cripto, "CHAVES_DIR", tmp_path)
    assert cripto._ler_chave("teste.key") == b"\x00\x01\x02"


def test_ler_chave_ausente_explica_como_gerar(monkeypatch, tmp_path):
    monkeypatch.setattr(cripto, "CHAVES_DIR", tmp_path)
    with pytest.raises(RuntimeError, match="gerar_chaves.py"):
        cripto._ler_chave("inexistente.key")


def test_importacao_carrega_chaves_validas(monkeypatch, dir_chaves):
    modulo = _importar_cripto_isolado(monkeypatch, dir_chaves)
    assert isinstance(modulo.CHAVE_PRIVADA, rsa.RSAPrivateKey)
    assert isinstance(modulo.CHAVE_PUBLICA, rsa.RSAPublicKey)


def test_importacao_falha_sem_chave(monkeypatch, dir_chaves, tmp_path):
    destino = _copiar_chaves(dir_chaves, tmp_path / "chaves")
    (destino / "hmac.key").unlink()
    with pytest.raises(RuntimeError, match="hmac.key"):
        _importar_cripto_isolado(monkeypatch, destino)


@pytest.mark.parametrize("arquivo", ["aes.key", "hmac.key"])
def test_importacao_falha_com_chave_simetrica_curta(monkeypatch, dir_chaves, tmp_path, arquivo):
    destino = _copiar_chaves(dir_chaves, tmp_path / "chaves")
    (destino / arquivo).write_bytes(b"\x00" * 16)
    with pytest.raises(RuntimeError, match="32 bytes"):
        _importar_cripto_isolado(monkeypatch, destino)


def test_importacao_falha_com_chave_que_nao_e_rsa(monkeypatch, dir_chaves, tmp_path):
    destino = _copiar_chaves(dir_chaves, tmp_path / "chaves")
    chave_ec = ec.generate_private_key(ec.SECP256R1())
    (destino / "rsa_privada.pem").write_bytes(
        chave_ec.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    with pytest.raises(RuntimeError, match="chaves RSA"):
        _importar_cripto_isolado(monkeypatch, destino)


# ------- AES-256-GCM -------------
def test_cifrar_e_decifrar_ida_e_volta():
    assert cripto.decifrar(cripto.cifrar("ana@exemplo.com")) == "ana@exemplo.com"


def test_cifrar_preserva_unicode():
    assert cripto.decifrar(cripto.cifrar("joão@exemplo.com.br")) == "joão@exemplo.com.br"


def test_cifrar_usa_nonce_aleatorio():
    primeiro, segundo = cripto.cifrar("ana@exemplo.com"), cripto.cifrar("ana@exemplo.com")
    assert primeiro != segundo
    assert primeiro[: cripto.TAMANHO_NONCE] != segundo[: cripto.TAMANHO_NONCE]


def test_cifrar_formato_nonce_texto_tag():
    texto = "ana@exemplo.com"
    # 12 bytes de nonce + texto cifrado (mesmo tamanho do claro) + 16 bytes de tag
    assert len(cripto.cifrar(texto)) == cripto.TAMANHO_NONCE + len(texto.encode()) + 16


def test_cifrar_nao_deixa_texto_claro():
    assert b"ana@exemplo.com" not in cripto.cifrar("ana@exemplo.com")


@pytest.mark.parametrize("posicao", [0, cripto.TAMANHO_NONCE, -1])
def test_decifrar_detecta_adulteracao(posicao):
    # Altera um byte do nonce, do texto cifrado e da tag
    cifrado = bytearray(cripto.cifrar("ana@exemplo.com"))
    cifrado[posicao] ^= 1
    with pytest.raises(InvalidTag):
        cripto.decifrar(bytes(cifrado))


def test_decifrar_recusa_outra_aad(dir_chaves):
    # Mesma chave e nonce, mas cifrado para outro uso: o AAD impede o reaproveitamento
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = b"\x00" * cripto.TAMANHO_NONCE
    chave = (dir_chaves / "aes.key").read_bytes()
    cifrado = nonce + AESGCM(chave).encrypt(nonce, b"ana@exemplo.com", b"outra.coluna")
    with pytest.raises(InvalidTag):
        cripto.decifrar(cifrado)


# ------- BLIND INDEX -------------
@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Ana@Exemplo.COM", "ana@exemplo.com"),
        ("  ana@exemplo.com\n", "ana@exemplo.com"),
        ("ａｎａ@exemplo.com", "ana@exemplo.com"),  # letras de largura total (NFKC)
    ],
)
def test_normalizar_email(entrada, esperado):
    assert cripto.normalizar_email(entrada) == esperado


def test_indice_email_e_hmac_sha256_do_email_normalizado(dir_chaves):
    chave = (dir_chaves / "hmac.key").read_bytes()
    esperado = hmac.new(chave, b"ana@exemplo.com", hashlib.sha256).digest()
    assert cripto.indice_email(" Ana@Exemplo.com ") == esperado


def test_indice_email_estavel_e_distinto():
    assert len(cripto.indice_email("ana@exemplo.com")) == 32
    assert cripto.indice_email("ana@exemplo.com") == cripto.indice_email("ANA@exemplo.com")
    assert cripto.indice_email("ana@exemplo.com") != cripto.indice_email("bia@exemplo.com")


def test_indice_email_nao_e_sha256_simples():
    # Sem a chave HMAC, não dá para testar uma lista de e-mails contra o índice
    assert cripto.indice_email("ana@exemplo.com") != hashlib.sha256(b"ana@exemplo.com").digest()


# ------- RSA-PSS -------------
def test_assinar_e_verificar():
    assinatura = cripto.assinar(b"dados")
    assert len(assinatura) == 384  # RSA 3072 bits
    assert cripto.verificar_assinatura(b"dados", assinatura)


def test_assinatura_pss_e_aleatoria():
    assert cripto.assinar(b"dados") != cripto.assinar(b"dados")


def test_verificar_assinatura_recusa_dado_alterado():
    assert not cripto.verificar_assinatura(b"dadoz", cripto.assinar(b"dados"))


def test_verificar_assinatura_recusa_assinatura_alterada():
    assinatura = bytearray(cripto.assinar(b"dados"))
    assinatura[10] ^= 1
    assert not cripto.verificar_assinatura(b"dados", bytes(assinatura))


def test_verificar_assinatura_recusa_outra_chave():
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    outra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pss = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)
    assert not cripto.verificar_assinatura(b"dados", outra.sign(b"dados", pss, hashes.SHA256()))


# ------- TIPO EmailCifrado -------------
def test_email_cifrado_configuracao():
    tipo = cripto.EmailCifrado()
    assert isinstance(tipo.impl, LargeBinary)
    assert tipo.cache_ok is True


def test_email_cifrado_grava_cifrado():
    gravado = cripto.EmailCifrado().process_bind_param("ana@exemplo.com", None)
    assert isinstance(gravado, bytes)
    assert b"ana@exemplo.com" not in gravado
    assert cripto.decifrar(gravado) == "ana@exemplo.com"


def test_email_cifrado_le_decifrado():
    lido = cripto.EmailCifrado().process_result_value(cripto.cifrar("ana@exemplo.com"), None)
    assert lido == "ana@exemplo.com"


def test_email_cifrado_aceita_memoryview():
    # O psycopg2 devolve bytea como memoryview
    valor = memoryview(cripto.cifrar("ana@exemplo.com"))
    assert cripto.EmailCifrado().process_result_value(valor, None) == "ana@exemplo.com"


def test_email_cifrado_preserva_nulo():
    tipo = cripto.EmailCifrado()
    assert tipo.process_bind_param(None, None) is None
    assert tipo.process_result_value(None, None) is None


def test_entidade_usuario_usa_email_cifrado_e_indice():
    colunas = entidades.Usuario.__table__.c
    assert isinstance(colunas.email.type, cripto.EmailCifrado)
    assert isinstance(colunas.email_indice.type, LargeBinary)
    assert colunas.email_indice.index is True
