# SealAuth

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy, Argon2 |
| Frontend | TypeScript, React, Vite, Tailwind, React Router |
| Dados | PostgreSQL 15 (via PgBouncer), Redis 7 |
| Infra | Docker Compose |

## Visão geral dos serviços

| Serviço | Container | URL no seu computador |
|---|---|---|
| Frontend | `seal_front` | http://localhost:3006 |
| API | `seal_backend` | http://localhost:8001 |
| Documentação da API (Swagger) | `seal_backend` | http://localhost:8001/docs |
| PostgreSQL | `seal_banco` | `localhost:5433` |
| PgBouncer, Redis | `pgbouncer_proxy`, `seal_redis` | apenas rede interna do Docker |

---

## 1. Pré-requisitos

Instale **antes** de continuar:

| Ferramenta | Versão recomendada | Para quê |
|---|---|---|
| [Docker Engine / Docker Desktop](https://docs.docker.com/get-docker/) | 24+ com **Compose v2** (`docker compose`, não `docker-compose`) | Roda todo o projeto |
| Git | qualquer recente | Clonar o repositório |
| OpenSSL | qualquer versão recente | Gerar o segredo do JWT (opcional: há fallback para o `.env`) |
| Make | qualquer | Atalhos de comandos (opcional; sem ele, use `docker compose` direto) |
| Node.js + Yarn | Node 22, Yarn 1.22 | **Só** se for editar o frontend com autocomplete na IDE |
| Python | 3.13+ | **Só** se for editar o backend com autocomplete na IDE |

Confira o Docker:

```bash
docker --version
docker compose version
```

> Windows: use WSL2 ou Git Bash para os comandos abaixo. O gerador de segredo também tem uma versão PowerShell (veja o passo 4).

## 2. Clonagem

```bash
git clone git@github.com:yoRitayo/SealAuth.git
cd SealAuth
```

Sem chave SSH configurada, use HTTPS:

```bash
git clone https://github.com/yoRitayo/SealAuth.git
cd SealAuth
```

## 3. Variáveis de ambiente

O arquivo modelo se chama **`.env.template`** (não `.env.example`). Copie-o e edite:

```bash
cp .env.template .env
```

O `.env` está no `.gitignore`: **nunca o commite**. Preencha estes campos obrigatórios:

| Variável | O que colocar |
|---|---|
| `BANCO_NOME` | Nome do banco, ex.: `seal_postgres` |
| `BANCO_USUARIO` | Usuário **admin** do banco, ex.: `guardiao_app`. Cria as tabelas e aplica as proteções |
| `BANCO_SENHA` | Senha do admin. Invente uma; não precisa vir de lugar nenhum |
| `BANCO_APP_USUARIO` | Usuário **restrito** usado pela API, ex.: `seal_app` |
| `BANCO_APP_SENHA` | Senha do usuário restrito. Gere uma: `openssl rand -hex 24` |
| `VITE_API_URL` | Troque `http://localhost:XXX` por `http://localhost:8001` |
| `COOKIE_SECURE` | `true` com HTTPS. Em desenvolvimento local, veja o Troubleshooting 3 |

Os demais valores do template já funcionam em desenvolvimento. `SMTP_*` pode ficar vazio (veja "Primeiro acesso").

> Não existe chave secreta de terceiros para obter: todos os segredos do projeto são gerados por você.

## 4. Segredo do JWT (obrigatório antes de subir)

O Compose monta o segredo do JWT como Docker secret a partir de `secrets/jwt_secret.txt`. **Sem esse arquivo, o `docker compose up` falha.** Gere-o, sempre a partir da **raiz do repositório**:

```bash
./scripts/gerar_jwt_secret.sh
```

Windows (PowerShell):

```powershell
.\scripts\gerar_jwt_secret.ps1
```

O script usa `openssl rand`; se o OpenSSL não existir, copia o `JWT_SECRET` do seu `.env` (por isso o passo 3 vem antes). Para gerar outro segredo, apague `secrets/jwt_secret.txt` e rode de novo — isso desloga todos os usuários.

## 5. Instalação das dependências

Para **rodar o projeto, não instale nada manualmente**: o Docker instala as dependências na construção das imagens (passo 6).

Instale localmente **somente** para ter autocomplete e checagem de tipos na IDE:

```bash
# Frontend
cd src/frontend && yarn install && cd ../..

# Backend
cd src/backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ../..
```

## 6. Subindo a aplicação

Um único comando sobe banco, PgBouncer, Redis, API e frontend:

```bash
make up
# equivalente a: docker compose up -d --build
```

Acompanhe até a API ficar pronta (procure `Application startup complete`):

```bash
make logs
```

Disponível em:

- **Aplicação:** http://localhost:3006
- **API / Swagger:** http://localhost:8001/docs

> **Atenção:** os containers **não** montam o código-fonte como volume. Depois de editar qualquer arquivo do backend ou do frontend, rode `make up` de novo para reconstruir a imagem. Sem isso você continua vendo o código antigo.

## Primeiro acesso

1. Abra http://localhost:3006/registrar e crie uma conta.
2. A conta nasce **pendente**: você precisa ativá-la pelo link do e-mail. Sem `SMTP_HOST` no `.env` (padrão em dev), **nenhum e-mail é enviado**: o link aparece nos logs do backend:

   ```bash
   make logs        # procure por "ativar-conta?token=..." e abra o link no navegador
   ```
3. Todo cadastro novo recebe o papel `usuario`. Para testar o painel de administrador, promova sua conta:

   ```bash
   make psql
   ```

   ```sql
   UPDATE "USUARIOS" SET papel = 'admin' WHERE nome_usuario = 'seu-usuario';
   ```

   Saia (`\q`), faça logout e login de novo.

O painel inicial depende do papel:

| Papel | Acesso |
|---|---|
| `admin` | Usuários (bloquear, desbloquear, mudar papel, excluir), alertas e bloqueios de IP (criar), logs |
| `analista` | Alertas e logs, **somente leitura** |
| `usuario` | Apenas o próprio perfil (nome de usuário e senha) |

## Comandos úteis

| Comando | O que faz |
|---|---|
| `make up` | Sobe (e reconstrói) tudo |
| `make down` | Derruba os containers, mantendo os dados |
| `make ps` | Status dos containers |
| `make logs` | Logs do backend (inclui os links de e-mail em dev) |
| `make shell-backend` / `shell-db` / `shell-redis` / `shell-frontend` | Terminal dentro do container |
| `make psql` | Cliente SQL no banco |
| `make redis-cli` | Cliente do Redis |
| `make help` | Lista todos os alvos |

## Estrutura do repositório

```
SealAuth/
├── docker-compose.yml
├── Makefile
├── .env.template
├── scripts/              # geração do segredo do JWT (sh e PowerShell)
├── secrets/              # gerado localmente, fora do git
└── src/
    ├── backend/
    │   ├── main.py             # app FastAPI, CORS e criação das tabelas
    │   ├── controllers/        # rotas, uma classe por recurso
    │   ├── schemas/            # DTOs (Pydantic) de entrada e saída
    │   ├── database/           # entidades SQLAlchemy, init.sql, protecoes.sql
    │   ├── seguranca.py        # Argon2, JWT, dependência do usuário logado
    │   ├── controle_acesso.py  # permissões por papel (RBAC)
    │   ├── redis_cliente.py    # sessões de refresh, rate limit, tokens de e-mail
    │   └── email_service.py    # envio de e-mails (HTML)
    └── frontend/
        ├── pages/              # telas (login, registro, painéis por papel)
        ├── services/           # cliente da API, contexto de autenticação, tipos
        ├── routes/
        └── style/              # componentes de UI
```

## Segurança: o que você precisa saber antes de mexer

- Os logs de auditoria são **imutáveis por design**: um trigger recusa `UPDATE` e `DELETE`. Não há (nem deve haver) rota para editá-los.
- A API conecta ao banco com um usuário **restrito**. Quem cria as tabelas é o usuário admin; mudanças de esquema passam por ele.
- `init.sql` roda **uma única vez**, na criação do volume do Postgres. `protecoes.sql` roda a cada start da API.
- O login tem limite de **7 tentativas por minuto** (por IP e por usuário) e bloqueia a conta por 15 minutos após 5 senhas erradas.
- Fora de `ENV=development`, a API **recusa** enviar e-mail sem `SMTP_HOST`, em vez de gravar tokens no log.

## Solução de problemas

### 1. `docker compose up` falha com erro sobre `secrets/jwt_secret.txt`

O arquivo do segredo não existe. Gere-o (passo 4) e suba de novo:

```bash
./scripts/gerar_jwt_secret.sh
make up
```

### 2. A API não sobe: `password authentication failed` ou `role "seal_app" does not exist`

Você alterou `BANCO_USUARIO`, `BANCO_SENHA` ou `BANCO_APP_SENHA` **depois** da primeira subida. Os usuários do banco são criados só na primeira criação do volume, então o `.env` novo não é aplicado ao banco existente.

Opção 1: voltar o `.env` aos valores originais. Opção 2 (**apaga todos os dados locais** do banco e do Redis):

```bash
docker compose down -v
make up
```

### 3. O login "funciona", mas a sessão cai ao recarregar a página

O cookie do refresh token é `Secure` quando `COOKIE_SECURE=true`, e navegadores costumam recusar cookies `Secure` em `http://` (alguns abrem exceção para `localhost`, outros não). Sem o cookie, a sessão não sobrevive ao recarregar. Se isso acontecer em desenvolvimento, ajuste no `.env`:

```env
COOKIE_SECURE=false
```

Depois `make up`. Nunca use `false` em produção.
