import os
import re
import shutil
import ssl
import subprocess
import tempfile
import time
from pathlib import Path
from urllib import request, parse, error
from urllib.parse import urlsplit
from uuid import uuid4

import pytest

# Precisa da API nesta máquina e do TShark; grava a tentativa no banco da API.
# Reprova enquanto a API rodar sem TLS: a senha aparece em texto legível no tráfego.
pytestmark = pytest.mark.e2e


TSHARK_WINDOWS = Path(r"C:\Program Files\Wireshark\tshark.exe")
LOCAIS = ("127.0.0.1", "localhost", "::1")


def localizar_tshark():
    # Ordem: variável TSHARK_PATH, PATH do sistema e instalação padrão do Windows
    for caminho in (os.getenv("TSHARK_PATH"), shutil.which("tshark"), str(TSHARK_WINDOWS)):
        if caminho and Path(caminho).exists():
            return caminho
    return None


def localizar_loopback(tshark):
    escolhida = os.getenv("TSHARK_INTERFACE")
    if escolhida:
        return escolhida

    resultado = subprocess.run(
        [tshark, "-D"],
        capture_output=True,
        text=True,
        check=True,
    )

    # Windows: \Device\NPF_Loopback; Linux: lo; macOS: lo0
    for linha in resultado.stdout.splitlines():
        if "loopback" in linha.lower():
            encontrado = re.match(r"^\s*\d+\.\s+(\S+)", linha)
            if encontrado:
                return encontrado.group(1)

    pytest.skip(
        "Interface de loopback nao encontrada no TShark "
        "(no Windows, instale o Npcap com suporte a loopback ou defina TSHARK_INTERFACE)."
    )


def test_senha_nao_deve_aparecer_no_trafego(api_url):
    endereco = urlsplit(api_url)
    if endereco.hostname not in LOCAIS:
        pytest.skip("A captura e feita no loopback: a API precisa estar nesta maquina.")

    tshark = localizar_tshark()
    if tshark is None:
        pytest.skip("TShark nao encontrado (instale o Wireshark ou defina TSHARK_PATH).")

    porta = endereco.port or (443 if endereco.scheme == "https" else 80)
    interface = localizar_loopback(tshark)
    # Senha única por execução: só conta o que este teste enviou
    senha = f"SenhaFicticiaT20_{uuid4().hex[:8]}"

    with tempfile.TemporaryDirectory() as pasta:
        captura = Path(pasta) / "t20.pcapng"

        # Captura a porta da API no loopback por 8 segundos
        processo = subprocess.Popen(
            [
                tshark,
                "-i", interface,
                "-f", f"tcp port {porta}",
                "-w", str(captura),
                "-a", "duration:8",
                "-q",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        try:
            # Dá tempo do TShark começar a capturar
            time.sleep(2)

            assert processo.poll() is None, (
                "TShark encerrou antes da requisicao: "
                f"{processo.stderr.read().decode(errors='replace')}"
            )

            dados = parse.urlencode({
                "username": "usuario_ficticio_t20",
                "password": senha,
            }).encode()

            requisicao = request.Request(
                f"{api_url}/auth/login",
                data=dados,
                method="POST",
            )

            # Com HTTPS e certificado autoassinado, a senha ainda precisa ser enviada para
            # o teste valer: aqui se avalia o sigilo do canal, não o certificado
            contexto = ssl._create_unverified_context() if endereco.scheme == "https" else None

            try:
                with request.urlopen(requisicao, timeout=5, context=contexto):
                    pass
            except error.HTTPError:
                pass  # o usuário não existe, então o 401 é esperado

            _, erros = processo.communicate(timeout=12)

        finally:
            if processo.poll() is None:
                processo.terminate()
                processo.wait(timeout=5)

        assert processo.returncode == 0, (
            f"Erro na captura: {erros.decode(errors='replace')}"
        )

        assert captura.exists() and captura.stat().st_size > 0, (
            "Nenhum arquivo de captura foi gerado."
        )

        resultado = subprocess.run(
            [
                tshark,
                "-r", str(captura),
                "-Y", f"tcp.dstport == {porta} && tcp.len > 0",
                "-T", "fields",
                "-e", "tcp.payload",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Junta os payloads TCP enviados para a API
        trafego = b"".join(
            bytes.fromhex(linha.strip().replace(":", ""))
            for linha in resultado.stdout.splitlines()
            if linha.strip()
        )

        assert trafego, "Nenhum dado enviado a API foi capturado."

        # Com HTTPS o pedido vai cifrado, então só dá para conferir o texto em HTTP
        if endereco.scheme == "http":
            assert b"POST /auth/login" in trafego, (
                "Requisicao de login nao capturada."
            )

        assert senha.encode() not in trafego, (
            "FALHA DE SEGURANCA T20: "
            "senha encontrada em texto legivel no trafego HTTP."
        )
