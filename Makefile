# ============================================================
# Makefile — Ferretería SaaS
# ============================================================

.PHONY: help \
        up up-d down restart \
        build build-backend build-frontend rebuild \
        logs logs-backend logs-frontend logs-db \
        ps shell-backend shell-db \
        migrate migration migrate-down migrate-history \
        deploy backup \
        create-admin create-user activate-org list-orgs

CYAN  := \033[0;36m
GREEN := \033[0;32m
RESET := \033[0m

.DEFAULT_GOAL := help

help: ## Muestra esta ayuda
	@echo ""
	@echo "  Ferretería SaaS — Comandos disponibles"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── Servicios ─────────────────────────────────────────────

up: ## Levanta todos los servicios con hot reload
	docker compose up

up-d: ## Levanta todos los servicios en background
	docker compose up -d

down: ## Detiene y elimina los contenedores
	docker compose down

down-v: ## Detiene contenedores y BORRA los datos (cuidado)
	@read -p "¿Borrar todos los datos? (y/N): " c && [ "$$c" = "y" ]
	docker compose down -v

restart: ## Reinicia todos los servicios
	docker compose restart

restart-backend: ## Reinicia solo el backend
	docker compose restart backend

restart-frontend: ## Reinicia solo el frontend
	docker compose restart frontend

ps: ## Ver estado de los contenedores
	docker compose ps

# ── Build ─────────────────────────────────────────────────

build: ## Construye todas las imágenes
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

logs: ## Logs de todos los servicios
	docker compose logs -f

logs-backend: ## Logs del backend
	docker compose logs -f backend

logs-frontend: ## Logs del frontend
	docker compose logs -f frontend

logs-db: ## Logs de la base de datos
	docker compose logs -f db

# ── Consolas ──────────────────────────────────────────────

shell-backend: ## Terminal dentro del contenedor backend
	docker compose exec backend bash

shell-db: ## Consola de PostgreSQL
	docker compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

# ── Migraciones ───────────────────────────────────────────

migrate: ## Aplica migraciones pendientes
	docker compose exec backend alembic upgrade head

migration: ## Genera migración (uso: make migration MSG="descripcion")
	@[ -n "$(MSG)" ] || (echo "❌ Uso: make migration MSG='descripcion'"; exit 1)
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Revierte la última migración
	docker compose exec backend alembic downgrade -1

migrate-history: ## Historial de migraciones
	docker compose exec backend alembic history --verbose

# ── Deploy y backup ───────────────────────────────────────

deploy: ## Deploy al VPS
	bash scripts/deploy.sh

backup: ## Backup de la base de datos
	bash scripts/backup.sh

# ── Usuarios y organizaciones ─────────────────────────────

create-admin: ## Hacer admin a usuario (uso: make create-admin EMAIL=x)
	@[ -n "$(EMAIL)" ] || (echo "❌ Uso: make create-admin EMAIL=tu@correo.com"; exit 1)
	docker compose exec backend python /app/scripts/make_admin.py "$(EMAIL)"

create-user: ## Crear usuario (uso: make create-user EMAIL=x NAME='x' ORG='x' PASS=x)
	@[ -n "$(EMAIL)" ] || (echo "❌ Falta EMAIL"; exit 1)
	@[ -n "$(NAME)"  ] || (echo "❌ Falta NAME";  exit 1)
	@[ -n "$(ORG)"   ] || (echo "❌ Falta ORG";   exit 1)
	@[ -n "$(PASS)"  ] || (echo "❌ Falta PASS";  exit 1)
	docker compose exec backend python /app/scripts/create_user.py "$(EMAIL)" "$(NAME)" "$(ORG)" "$(PASS)"

activate-org: ## Activar suscripción (uso: make activate-org EMAIL=x)
	@[ -n "$(EMAIL)" ] || (echo "❌ Uso: make activate-org EMAIL=correo@cliente.com"; exit 1)
	docker compose exec backend python /app/scripts/activate_org.py "$(EMAIL)"

list-orgs: ## Listar organizaciones y su estado
	docker compose exec backend python /app/scripts/list_orgs.py
