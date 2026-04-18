# ============================================================
# Makefile — Comandos del proyecto
# ============================================================

.PHONY: help dev dev-d down down-v logs logs-backend logs-db \
        shell-backend shell-db migrate migration migrate-down \
        migrate-history build prod prod-down prod-logs deploy backup \
        restart restart-backend ps \
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

# ── Desarrollo ────────────────────────────────────────────

dev: ## Levanta el entorno de desarrollo (con hot reload)
	@echo "$(GREEN)Levantando entorno de desarrollo...$(RESET)"
	docker compose up --build

dev-d: ## Levanta en background (detached)
	docker compose up --build -d

down: ## Detiene y elimina los contenedores (datos persisten)
	docker compose down

down-v: ## Detiene y elimina contenedores Y volúmenes (BORRA DATOS)
	@echo "⚠️  Esto borrará todos los datos de la base de datos"
	@read -p "¿Estás seguro? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker compose down -v

restart: ## Reinicia todos los servicios sin rebuild
	docker compose restart

restart-backend: ## Reinicia solo el backend
	docker compose restart backend

ps: ## Ver estado de los contenedores
	docker compose ps

# ── Logs ──────────────────────────────────────────────────

logs: ## Logs de todos los servicios
	docker compose logs -f

logs-backend: ## Logs solo del backend
	docker compose logs -f backend

logs-db: ## Logs solo de la base de datos
	docker compose logs -f db

# ── Shells interactivos ───────────────────────────────────

shell-backend: ## Abre bash dentro del contenedor del backend
	docker compose exec backend bash

shell-db: ## Abre psql dentro del contenedor de postgres
	docker compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

# ── Migraciones ───────────────────────────────────────────

migrate: ## Aplica todas las migraciones pendientes
	docker compose exec backend alembic upgrade head

migration: ## Genera migración (uso: make migration MSG="descripcion")
	@[ -n "$(MSG)" ] || (echo "❌ Falta MSG. Uso: make migration MSG='descripcion'"; exit 1)
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Revierte la última migración
	docker compose exec backend alembic downgrade -1

migrate-history: ## Muestra el historial de migraciones
	docker compose exec backend alembic history --verbose

# ── Build y producción ────────────────────────────────────

build: ## Construye las imágenes de producción
	docker compose -f docker-compose.prod.yml build

prod: ## Levanta el entorno de producción
	docker compose -f docker-compose.prod.yml up -d

prod-down: ## Detiene producción
	docker compose -f docker-compose.prod.yml down

prod-logs: ## Logs de producción
	docker compose -f docker-compose.prod.yml logs -f

# ── Deploy ────────────────────────────────────────────────

deploy: ## Deploy completo al VPS (requiere SSH configurado)
	@echo "$(GREEN)Iniciando deploy...$(RESET)"
	bash scripts/deploy.sh

# ── Backup ───────────────────────────────────────────────

backup: ## Crea un backup de la base de datos
	bash scripts/backup.sh

# ── Gestión de usuarios ───────────────────────────────────

create-admin: ## Hacer admin a usuario existente (uso: make create-admin EMAIL=x)
	@[ -n "$(EMAIL)" ] || (echo "❌ Uso: make create-admin EMAIL=tu@correo.com"; exit 1)
	docker compose exec backend python scripts/make_admin.py "$(EMAIL)"

create-user: ## Crear usuario (uso: make create-user EMAIL=x NAME='x' ORG='x' PASS=x)
	@[ -n "$(EMAIL)" ] || (echo "❌ Falta EMAIL"; exit 1)
	@[ -n "$(NAME)"  ] || (echo "❌ Falta NAME";  exit 1)
	@[ -n "$(ORG)"   ] || (echo "❌ Falta ORG";   exit 1)
	@[ -n "$(PASS)"  ] || (echo "❌ Falta PASS";  exit 1)
	docker compose exec backend python scripts/create_user.py "$(EMAIL)" "$(NAME)" "$(ORG)" "$(PASS)"

activate-org: ## Activar suscripción de org (uso: make activate-org EMAIL=x)
	@[ -n "$(EMAIL)" ] || (echo "❌ Uso: make activate-org EMAIL=correo@cliente.com"; exit 1)
	docker compose exec backend python scripts/activate_org.py "$(EMAIL)"

list-orgs: ## Listar todas las organizaciones y su estado
	docker compose exec backend python scripts/list_orgs.py
