#!/bin/bash
# ============================================================
# scripts/deploy.sh — Deploy al VPS
# ============================================================
#
# Qué hace este script:
#   1. Conecta al VPS por SSH
#   2. Hace pull del código más reciente
#   3. Reconstruye las imágenes Docker
#   4. Reinicia los servicios con zero-downtime
#   5. Aplica migraciones pendientes
#
# Requisitos previos:
#   - SSH configurado: ssh-copy-id usuario@tu-vps-ip
#   - Variables de entorno definidas abajo
#   - .env de producción en el VPS en ~/ferreteria-saas/.env
#
# Uso: make deploy
#      o directamente: bash scripts/deploy.sh
# ============================================================

set -e  # Parar si cualquier comando falla

# ── Configuración — EDITAR ANTES DE USAR ──────────────────
VPS_USER="root"           # Usuario SSH del VPS
VPS_HOST="tu-ip-aqui"    # IP o dominio del VPS
VPS_DIR="/opt/ferreteria-saas"  # Directorio en el VPS
GIT_BRANCH="main"         # Rama a deployar
# ──────────────────────────────────────────────────────────

# Colores
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
RESET='\033[0m'

echo -e "${CYAN}🚀 Iniciando deploy a ${VPS_HOST}...${RESET}"

# Verificar que el host está definido
if [ "$VPS_HOST" = "tu-ip-aqui" ]; then
    echo -e "${RED}❌ Error: Configura VPS_HOST en scripts/deploy.sh${RESET}"
    exit 1
fi

# Ejecutar comandos en el VPS vía SSH
# El bloque entre EOF se ejecuta remotamente, no localmente
ssh "$VPS_USER@$VPS_HOST" << EOF
    set -e
    
    echo "📂 Cambiando al directorio del proyecto..."
    cd "$VPS_DIR"
    
    echo "📥 Actualizando código..."
    git pull origin "$GIT_BRANCH"
    
    echo "🔨 Reconstruyendo imágenes..."
    docker compose -f docker-compose.prod.yml build
    
    echo "🔄 Reiniciando servicios..."
    docker compose -f docker-compose.prod.yml up -d
    
    echo "🗃️  Aplicando migraciones..."
    docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
    
    echo "🧹 Limpiando imágenes antiguas..."
    docker image prune -f
    
    echo "✅ Deploy completado"
EOF

echo -e "${GREEN}✅ Deploy exitoso${RESET}"
