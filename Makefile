# Atalhos para o docker compose
# Usem assim: make <alvo> 

.PHONY: help up down restart ps logs shell-backend shell-db shell-redis shell-frontend psql redis-cli test test-unit test-integration test-e2e test-all test-watch test-coverage

help:  ## lista os alvos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

up:  ## sobe todos os serviços em background
	docker compose -f docker-compose.yml up -d --build

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

test:  ## roda todos os testes (exceto E2E)
	docker compose exec backend pytest -v

test-unit:  ## roda apenas testes unitários
	docker compose exec backend pytest tests/unit -v

test-integration:  ## roda apenas testes de integração
	docker compose exec backend pytest tests/integration -v

test-e2e:  ## roda testes E2E 
	docker compose exec backend sh -c 'SEALAUTH_E2E=1 pytest tests -v -m e2e'

test-all:  ## roda todos os testes incluindo E2E
	docker compose exec backend sh -c 'SEALAUTH_E2E=1 pytest tests -v'

test-watch:  ## roda testes em modo watch 
	docker compose exec backend pytest-watch

test-coverage:  ## gera relatório de cobertura de testes
	docker compose exec backend pytest --cov=src/backend --cov-report=html --cov-report=term
