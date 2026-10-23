# Testes de segurança (E2E)

Testes que atacam a API **de verdade**, sem dublês. Por isso ficam desligados por padrão e só rodam com `SEALAUTH_E2E=1`.

| ID | Arquivo | O que verifica | Resultado esperado hoje |
|---|---|---|---|
| SEC-1 | `test_injecao_sql.py` | Login com `' OR '1'='1' --` no usuário recebe 401 | Passa |
| SEC-2 | `test_seguranca_trafego.py` | A senha não aparece no tráfego capturado com o TShark | **Reprova**: a API roda sem TLS e a senha vai em texto legível |

## Atenção

- Cada execução faz login na API e grava as tentativas no banco dela. **Use só um ambiente de desenvolvimento ou descartável, nunca produção.**
- O login tem rate limit de 7 tentativas por minuto. Se aparecer HTTP 429, espere 1 minuto e rode de novo.

## Pré-requisitos

1. A stack no ar: `make up` (a API fica em `http://127.0.0.1:8001`).
2. Python 3.11 ou superior com as dependências do backend e o pytest, porque o `tests/conftest.py` importa o backend:
   ```
   pip install -r src/backend/requirements.txt pytest
   ```
3. Só para o SEC-2: o TShark, que vem com o Wireshark.
   - **Windows:** Wireshark com o **Npcap**, marcando o suporte a loopback na instalação.
   - **Linux:** `sudo apt install tshark` e permissão de captura (`sudo usermod -aG wireshark $USER`, depois sair e entrar de novo na sessão).
   - **macOS:** `brew install --cask wireshark` (já inclui a permissão de captura).

Sem o TShark ou sem a API no ar, o teste é **pulado** e o motivo aparece com `-rs`. Isso não é uma aprovação.

## Como rodar

Na raiz do repositório:

**Windows (PowerShell)**
```powershell
$env:SEALAUTH_E2E = "1"
python -m pytest tests/security -v -rs
```

**Linux ou macOS**
```bash
SEALAUTH_E2E=1 python -m pytest tests/security -v -rs
```

## Variáveis opcionais

| Variável | Padrão | Para quê |
|---|---|---|
| `SEALAUTH_API_URL` | `http://127.0.0.1:8001` | Testar uma API em outra porta. O SEC-2 exige uma API nesta máquina. |
| `TSHARK_PATH` | `PATH` do sistema ou `C:\Program Files\Wireshark\tshark.exe` | Caminho do `tshark`, se ele estiver em outro lugar |
| `TSHARK_INTERFACE` | Detectada pelo nome "loopback" | Interface de captura, se a detecção falhar (ex.: `lo`) |
