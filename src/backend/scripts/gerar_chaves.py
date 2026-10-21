# Gera as chaves do backend em SealAuth/keys/ (fora do git):
#   aes.key, hmac.key        -> 32 bytes aleatórios (AES-256-GCM do e-mail e blind index)
#   rsa_privada.pem/.pub     -> par RSA 3072 (JWT RS256 e assinatura dos logs)
#   cert.pem, cert.key       -> certificado HTTPS autoassinado para localhost
# Uso, a partir da raiz do repositório: python src/backend/scripts/gerar_chaves.py [--forcar]
import argparse
import ipaddress
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

DESTINO_PADRAO = Path(__file__).resolve().parents[3] / "keys"


def _pem_privada(chave: rsa.RSAPrivateKey) -> bytes:
    return chave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _certificado(chave: rsa.RSAPrivateKey) -> bytes:
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    agora = datetime.now(UTC)
    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)  # autoassinado: emissor = sujeito
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora)
        .not_valid_after(agora + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                ]
            ),
            critical=False,
        )
        .sign(chave, hashes.SHA256())
    )
    return certificado.public_bytes(serialization.Encoding.PEM)


def gerar(destino: Path, forcar: bool) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    existentes = [n for n in ("aes.key", "rsa_privada.pem") if (destino / n).exists()]
    if existentes and not forcar:
        print(f"Chaves já existem em {destino} (use --forcar para gerar outras)")
        return

    rsa_app = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    rsa_tls = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    arquivos = {
        "aes.key": os.urandom(32),
        "hmac.key": os.urandom(32),
        "rsa_privada.pem": _pem_privada(rsa_app),
        "rsa_publica.pem": rsa_app.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ),
        "cert.key": _pem_privada(rsa_tls),
        "cert.pem": _certificado(rsa_tls),
    }
    for nome, conteudo in arquivos.items():
        caminho = destino / nome
        caminho.write_bytes(conteudo)
        if nome != "rsa_publica.pem" and nome != "cert.pem":
            caminho.chmod(0o600)  # sem efeito real no Windows
        print(f"  {caminho}")
    print("Chaves geradas. Trocar as chaves invalida os e-mails cifrados e os logs já assinados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera as chaves do SealAuth")
    parser.add_argument("--destino", type=Path, default=DESTINO_PADRAO)
    parser.add_argument("--forcar", action="store_true", help="sobrescreve chaves existentes")
    argumentos = parser.parse_args()
    gerar(argumentos.destino, argumentos.forcar)
