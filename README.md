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
| Git | qualquer versão recente | Clonar o repositório |
| OpenSSL | qualquer versão recente | Gerar o segredo do JWT (opcional: há fallback para o `.env`) |
| Make | qualquer versão | Atalhos de comandos (opcional; sem ele, use `docker compose`) |
| Node.js + Yarn | Node 22, Yarn 1.22 | Editar o frontend |
| Python | 3.13+ | Editar o backend |

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

## 4. Segredos: JWT e chaves criptográficas (obrigatório antes de subir)

São dois passos, sempre a partir da **raiz do repositório**. Sem eles a API não sobe.

### 4.1 Chaves do backend (`keys/`)

A API cifra e-mails (AES-256), assina logs de auditoria (RSA) e lê essas chaves da pasta `keys/`, que fica fora do git. Gere-as uma vez:

```bash
pip install cryptography          # só se ainda não tiver (ou use o .venv do passo 5)
python src/backend/scripts/gerar_chaves.py
```

O script não sobrescreve chaves existentes. `--forcar` gera outras, mas **os e-mails já cifrados e os logs já assinados deixam de ser legíveis/verificáveis**: use apenas em banco vazio.

### 4.2 Segredo do JWT

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

> O passo 4.1 precisa do pacote `cryptography` no Python do seu computador. Se preferir, faça o passo 5 (venv) antes dele.

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

## Modo desenvolvimento x produção

O `docker-compose.yml` e os Dockerfiles vêm configurados para **desenvolvimento** (API com `--reload`, frontend com `yarn dev`). Para produção, siga o passo a passo acima e ajuste:

### Checklist de produção

1. **`.env` de produção**, com valores diferentes dos de dev:

   | Variável | Valor em produção |
   |---|---|
   | `AMBIENTE_PYTHON` | `production` (qualquer valor diferente de `development` exige SMTP) |
   | `VITE_AMBIENTE_NODE` | `production` |
   | `COOKIE_SECURE` | `true` |
   | `FRONTEND_URL` | URL pública do frontend com `https://` (é a única origem aceita pelo CORS) |
   | `VITE_API_URL` | URL pública da API com `https://` |
   | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_SENHA`, `SMTP_REMETENTE` | Servidor de e-mail real. Sem `SMTP_HOST` a API recusa enviar e ninguém ativa a conta |
   | `BANCO_SENHA`, `BANCO_APP_SENHA` | Senhas fortes e únicas (`openssl rand -hex 24`) |

2. **Segredos novos** (nunca reaproveite os de dev): rode os passos 3 e 4 no servidor. Guarde um backup de `keys/` e `secrets/` em local seguro: sem `keys/`, os e-mails cifrados e a verificação dos logs se perdem.
3. **HTTPS na frente da aplicação.** Use um proxy reverso (Nginx, Caddy, Traefik) com certificado válido apontando para as portas `3006` (frontend) e `8001` (API). Sem HTTPS, `COOKIE_SECURE=true` impede o login de manter a sessão.
4. **Não exponha o banco.** Remova a linha `"5433:5432"` do serviço `db` no `docker-compose.yml` e deixe o firewall liberando só 80/443.
5. **Retire o modo de desenvolvimento das imagens:** troque `--reload` por `--workers 2` (ou mais) no `CMD` de `src/backend/Dockerfile` e, no frontend, gere o build (`yarn build`) e sirva a pasta `dist/` por um servidor estático em vez de `yarn dev`.
6. Suba e confira:

   ```bash
   ./scripts/gerar_jwt_secret.sh
   make up
   make ps
   make logs
   ```
7. Crie sua conta pela tela de registro, ative-a pelo e-mail e promova-a a `admin` (veja "Primeiro acesso", passo 3). Depois, não deixe contas de teste no banco.

### Atualizando uma instalação existente

```bash
git pull
make up          # reconstrói as imagens com o código novo
```

Os dados ficam nos volumes `pgdata` e `redisdata` e sobrevivem ao `make up` e ao `make down`. Só `docker compose down -v` os apaga.

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

O arquivo do segredo não existe. Gere-o (passo 4.2) e suba de novo:

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

### 4. A API cai logo ao subir com `Chave ... não encontrada: rode scripts/gerar_chaves.py`

A pasta `keys/` está vazia ou não existe. Gere as chaves (passo 4.1) e suba de novo:

```bash
python src/backend/scripts/gerar_chaves.py
make up
```

### 5. Cadastro ou login deram "não foi possível conectar ao servidor", ou o navegador mostra erro de CORS

- Confira se a API está de pé: `make ps` e abra http://localhost:8001/docs.
- `VITE_API_URL` precisa ser `http://localhost:8001` (o template vem com `XXX`).
- `FRONTEND_URL` precisa ser **exatamente** a URL que você abre no navegador (mesma porta, sem barra no fim). `127.0.0.1` e `localhost` contam como origens diferentes.

Depois de mudar o `.env`, rode `make up`: as variáveis só são lidas na criação dos containers.

### 6. A conta não ativa: o e-mail nunca chega

Sem `SMTP_HOST`, em desenvolvimento, o link fica nos logs (`make logs`, procure `ativar-conta?token=`). Fora de `development`, a API **recusa** enviar sem SMTP: configure o servidor de e-mail. O token expira em `ATIVACAO_TOKEN_TTL_HORAS`; se venceu, peça um novo link pelo endpoint de reenvio de ativação (`POST /auth/reenviar-ativacao`, veja o Swagger em `/docs`).

### 7. "Muitas tentativas" ou conta bloqueada nos testes

O login limita 7 tentativas por minuto e bloqueia a conta por 15 minutos após 5 senhas erradas. Para liberar na hora em desenvolvimento:

```bash
make redis-cli        # depois: FLUSHALL   (apaga também as sessões)
make psql             # depois: UPDATE "USUARIOS" SET status = 'ativo', falhas_consecutivas = 0, bloqueado_ate = NULL WHERE nome_usuario = 'seu-usuario';
```

### 8. Porta já em uso (`3006`, `8001` ou `5433`)

Outro programa (ou outro Postgres local) usa a porta. Pare-o, ou troque o lado esquerdo do mapeamento em `docker-compose.yml` (ex.: `"5434:5432"`). Se mudar a `8001`, ajuste `VITE_API_URL` e, se mudar a `3006`, ajuste `FRONTEND_URL`.

### 9. Mudei o código e nada mudou

Os containers não montam o código como volume. Rode `make up` para reconstruir a imagem. Se ainda assim parecer antigo, force: `docker compose build --no-cache backend frontend && make up`.

### 10. Alterei o `init.sql` ou as tabelas e o banco não reflete

`init.sql` só roda quando o volume do Postgres é criado. Em desenvolvimento, recrie o banco com `docker compose down -v && make up` (**apaga os dados**). Em produção, aplique a mudança com `make psql`.

### 11. Erros de permissão em `secrets/` ou `keys/` no Linux

O script do JWT cria o arquivo com permissão `600`. Se o container não conseguir ler, confira o dono: `ls -l secrets keys`. Não use `chmod 777`; ajuste o dono para o seu usuário.
