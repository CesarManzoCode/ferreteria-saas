# ============================================================
# Makefile — Ferretería SaaS
# ============================================================

.PHONY: help \
        up up-d down down-v restart restart-backend restart-frontend \
        build build-backend build-frontend rebuild rebuild-backend rebuild-frontend \
        logs logs-backend logs-frontend logs-db \
        ps shell-backend shell-db \
        migrate migration migrate-down migrate-history \
        prod prod-down prod-logs prod-restart \
        deploy backup \
        create-admin create-user activate-org list-orgs

CYAN  := \033[0;36m
GREEN := \033[0;32m
YELLOW:= \033[0;33m
RED   := \033[0;31m
RESET := \033[0m

.DEFAULT_GOAL := help

help: ## Muestra esta ayuda
	@echo ""
	@echo "  Ferretería SaaS — Comandos disponibles"
	@echo ""
	@echo "  $(CYAN)── Desarrollo ────────────────────────────────────$(RESET)"
	@grep -E '^(up|up-d|down|down-v|restart|restart-backend|restart-frontend|ps):.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "  $(CYAN)── Build ──────────────────────────────────────────$(RESET)"
	@grep -E '^(build|build-backend|build-frontend|rebuild|rebuild-backend|rebuild-frontend):.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "  $(CYAN)── Logs y consolas ───────────────────────────────$(RESET)"
	@grep -E '^(logs|logs-backend|logs-frontend|logs-db|shell-backend|shell-db):.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "  $(CYAN)── Migraciones ───────────────────────────────────$(RESET)"
	@grep -E '^(migrate|migration|migrate-down|migrate-history):.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "  $(CYAN)── Producción ────────────────────────────────────$(RESET)"
	@grep -E '^(prod|prod-down|prod-logs|prod-restart|deploy|backup):.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "  $(CYAN)── Usuarios ──────────────────────────────────────$(RESET)"
	@grep -E '^(create-admin|create-user|activate-org|list-orgs):.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── Desarrollo ────────────────────────────────────────────

up: ## Levanta todos los servicios con hot reload
	docker compose up

up-d: ## Levanta todos los servicios en background
	docker compose up -d

down: ## Detiene y elimina los contenedores (datos persisten)
	docker compose down

down-v: ## ⚠️  Detiene contenedores y BORRA todos los datos
	@echo "$(RED)⚠️  Esto borrará todos los datos de la base de datos$(RESET)"
	@read -p "¿Estás seguro? (y/N): " c && [ "$$c" = "y" ]
	docker compose down -v

restart: ## Reinicia todos los servicios sin rebuild
	docker compose restart

restart-backend: ## Reinicia solo el backend
	docker compose restart backend

restart-frontend: ## Reinicia solo el frontend
	docker compose restart frontend

ps: ## Ver estado de los contenedores
	docker compose ps

# ── Build ─────────────────────────────────────────────────

build: ## Construye todas las imágenes (dev)
	docker compose build

build-backend: ## Construye solo la imagen del backend
	docker compose build backend

build-frontend: ## Construye solo la imagen del frontend
	docker compose build frontend

rebuild: ## Reconstruye todo desde cero sin cache
	docker compose build --no-cache

rebuild-backend: ## Reconstruye solo el backend sin cache
	docker compose build --no-cache backend

rebuild-frontend: ## Reconstruye solo el frontend sin cache
	docker compose build --no-cache frontend

# ── Logs ──────────────────────────────────────────────────

logs: ## Logs de todos los servicios en tiempo real
	docker compose logs -f

logs-backend: ## Logs del backend
	docker compose logs -f backend

logs-frontend: ## Logs del frontend
	docker compose logs -f frontend

logs-db: ## Logs de la base de datos
	docker compose logs -f db

# ── Consolas interactivas ─────────────────────────────────

shell-backend: ## Terminal dentro del contenedor backend
	docker compose exec backend bash

shell-db: ## Consola psql de PostgreSQL
	docker compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

# ── Migraciones ───────────────────────────────────────────

migrate: ## Aplica migraciones pendientes
	docker compose exec backend alembic upgrade head

migration: ## Genera migración (uso: make migration MSG="descripcion")
	@[ -n "$(MSG)" ] || (echo "$(RED)❌ Uso: make migration MSG='descripcion'$(RESET)"; exit 1)
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Revierte la última migración
	docker compose exec backend alembic downgrade -1

migrate-history: ## Historial de migraciones
	docker compose exec backend alembic history --verbose

# ── Producción ────────────────────────────────────────────

prod: ## Levanta el entorno de producción
	docker compose -f docker-compose.prod.yml up -d

prod-down: ## Detiene producción
	docker compose -f docker-compose.prod.yml down

prod-logs: ## Logs de producción en tiempo real
	docker compose -f docker-compose.prod.yml logs -f

prod-restart: ## Reinicia producción sin rebuild
	docker compose -f docker-compose.prod.yml restart

deploy: ## Deploy completo al VPS (git pull + rebuild + restart)
	bash scripts/deploy.sh

backup: ## Crea backup de la base de datos
	bash scripts/backup.sh

# ── Gestión de usuarios ───────────────────────────────────

create-admin: ## Hacer admin a usuario existente (uso: make create-admin EMAIL=x)
	@[ -n "$(EMAIL)" ] || (echo "$(RED)❌ Uso: make create-admin EMAIL=tu@correo.com$(RESET)"; exit 1)
	docker compose exec backend python /app/scripts/make_admin.py "$(EMAIL)"

create-user: ## Crear usuario (uso: make create-user EMAIL=x NAME='x' ORG='x' PASS=x)
	@[ -n "$(EMAIL)" ] || (echo "$(RED)❌ Falta EMAIL$(RESET)"; exit 1)
	@[ -n "$(NAME)"  ] || (echo "$(RED)❌ Falta NAME$(RESET)";  exit 1)
	@[ -n "$(ORG)"   ] || (echo "$(RED)❌ Falta ORG$(RESET)";   exit 1)
	@[ -n "$(PASS)"  ] || (echo "$(RED)❌ Falta PASS$(RESET)";  exit 1)
	docker compose exec backend python /app/scripts/create_user.py "$(EMAIL)" "$(NAME)" "$(ORG)" "$(PASS)"

activate-org: ## Activar suscripción de org (uso: make activate-org EMAIL=x)
	@[ -n "$(EMAIL)" ] || (echo "$(RED)❌ Uso: make activate-org EMAIL=correo@cliente.com$(RESET)"; exit 1)
	docker compose exec backend python /app/scripts/activate_org.py "$(EMAIL)"

list-orgs: ## Listar todas las organizaciones y su estado
	docker compose exec backend python /app/scripts/list_orgs.py
