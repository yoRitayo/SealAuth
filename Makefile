# Atalhos para o docker compose
# Usem assim: make <alvo> 

.PHONY: help up down restart ps logs shell-backend shell-db shell-redis shell-frontend psql redis-cli

help:  ## lista os alvos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

up:  ## sobe todos os serviços em background
	docker compose up -d --build

down:  ## derruba os serviços (mantém os volumes)
	docker compose down

restart:  ## reinicia o backend
	docker compose restart backend

ps:  ## status dos containers
	docker compose ps

logs:  ## acompanha os logs do backend
	docker compose logs -f backend

shell-backend:  ## terminal dentro do container do backend
	docker compose exec backend sh

shell-db:  ## terminal dentro do container do Postgres
	docker compose exec db sh

psql:  ## cliente psql conectado ao banco (usa as variáveis do próprio container)
	docker compose exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

shell-redis:  ## terminal dentro do container do Redis
	docker compose exec redis sh

redis-cli:  ## redis-cli conectado ao Redis do compose
	docker compose exec redis redis-cli

shell-frontend:  ## terminal dentro do container do frontend
	docker compose exec frontend sh
