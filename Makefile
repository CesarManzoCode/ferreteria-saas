# ============================================================
# Makefile — Comandos del proyecto
# ============================================================
#
# Uso: make <comando>
# Ejemplo: make dev, make logs, make migrate
#
# .PHONY declara targets que no son archivos reales.
# Sin esto, si existe un archivo llamado "dev", make se confunde.
#
.PHONY: help dev down logs shell-backend shell-db migrate \
        migration build prod deploy backup

# ── Colores para output legible ───────────────────────────
CYAN  := \033[0;36m
GREEN := \033[0;32m
RESET := \033[0m

# ── Comando por default al escribir solo 'make' ───────────
.DEFAULT_GOAL := help

help: ## Muestra esta ayuda
	@echo ""
	@echo "  Ferretería SaaS — Comandos disponibles"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── Desarrollo ────────────────────────────────────────────

dev: ## Levanta todo el entorno de desarrollo (con hot reload)
	@echo "$(GREEN)Levantando entorno de desarrollo...$(RESET)"
	docker compose up --build

dev-d: ## Levanta en background (detached)
	docker compose up --build -d

down: ## Detiene y elimina los contenedores (datos persisten en volúmenes)
	docker compose down

down-v: ## Detiene y elimina contenedores Y volúmenes (BORRA LOS DATOS)
	@echo "⚠️  Esto borrará todos los datos de la base de datos"
	@read -p "¿Estás seguro? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker compose down -v

logs: ## Muestra logs de todos los servicios
	docker compose logs -f

logs-backend: ## Muestra solo logs del backend
	docker compose logs -f backend

logs-db: ## Muestra solo logs de la base de datos
	docker compose logs -f db

# ── Shells interactivos ───────────────────────────────────

shell-backend: ## Abre bash dentro del contenedor del backend
	docker compose exec backend bash

shell-db: ## Abre psql dentro del contenedor de postgres
	docker compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

# ── Base de datos y migraciones ───────────────────────────

migrate: ## Aplica todas las migraciones pendientes
	docker compose exec backend alembic upgrade head

migration: ## Genera una nueva migración (uso: make migration MSG="descripcion")
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

# ── Deploy al VPS ─────────────────────────────────────────

deploy: ## Deploy completo al VPS (requiere SSH configurado)
	@echo "$(GREEN)Iniciando deploy...$(RESET)"
	bash scripts/deploy.sh

# ── Backup ───────────────────────────────────────────────

backup: ## Crea un backup de la base de datos
	bash scripts/backup.sh

# ── Gestión de usuarios ───────────────────────────────────

create-admin: ## Hacer admin a un usuario existente (uso: make create-admin EMAIL=tu@email.com)
	@[ -n "$(EMAIL)" ] || (echo "❌ Falta EMAIL. Uso: make create-admin EMAIL=tu@correo.com"; exit 1)
	docker compose exec backend python -c "
import sys; sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.models.user import User
db = SessionLocal()
user = db.query(User).filter(User.email == '$(EMAIL)').first()
if not user:
    print('❌ Usuario no encontrado: $(EMAIL)')
    sys.exit(1)
user.role = 'admin'
db.commit()
print(f'✅ {user.full_name} ({user.email}) ahora es admin')
"

create-user: ## Crear usuario desde consola (uso: make create-user EMAIL=x NAME=x ORG=x PASS=x)
	@[ -n "$(EMAIL)" ] || (echo "❌ Falta EMAIL"; exit 1)
	@[ -n "$(NAME)"  ] || (echo "❌ Falta NAME";  exit 1)
	@[ -n "$(ORG)"   ] || (echo "❌ Falta ORG";   exit 1)
	@[ -n "$(PASS)"  ] || (echo "❌ Falta PASS";  exit 1)
	docker compose exec backend python -c "
import sys, uuid; sys.path.insert(0, '.')
from slugify import slugify
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User
db = SessionLocal()
if db.query(User).filter(User.email == '$(EMAIL)').first():
    print('❌ Email ya registrado')
    sys.exit(1)
slug = slugify('$(ORG)')
org = Organization(name='$(ORG)', slug=slug)
org.set_trial()
db.add(org); db.flush()
user = User(organization_id=org.id, email='$(EMAIL)', hashed_password=hash_password('$(PASS)'), full_name='$(NAME)')
db.add(user); db.commit()
print(f'✅ Usuario creado: $(EMAIL) en org "$(ORG)"')
"

activate-org: ## Activar suscripción de una org (uso: make activate-org EMAIL=admin@org.com)
	@[ -n "$(EMAIL)" ] || (echo "❌ Falta EMAIL del usuario de esa org"; exit 1)
	docker compose exec backend python -c "
import sys; sys.path.insert(0, '.')
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.user import User
from sqlalchemy.orm import joinedload
db = SessionLocal()
user = db.query(User).options(joinedload(User.organization)).filter(User.email == '$(EMAIL)').first()
if not user:
    print('❌ Usuario no encontrado')
    sys.exit(1)
org = user.organization
org.subscription_status = 'active'
org.subscribed_at = datetime.now(timezone.utc)
db.commit()
print(f'✅ Org "{org.name}" activada')
"

list-orgs: ## Listar todas las organizaciones y su estado
	docker compose exec backend python -c "
import sys; sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.models.organization import Organization
db = SessionLocal()
orgs = db.query(Organization).order_by(Organization.created_at.desc()).all()
print(f'\n  {"Nombre":<30} {"Status":<12} {"Trial vence":<22} {"Activa"}')
print('  ' + '-'*75)
for o in orgs:
    trial = o.trial_ends_at.strftime("%d %b %Y %H:%M") if o.trial_ends_at else '-'
    print(f'  {o.name:<30} {o.subscription_status:<12} {trial:<22} {o.is_active}')
print()
"
