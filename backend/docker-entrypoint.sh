#!/bin/bash
# ============================================================
# docker-entrypoint.sh
# ============================================================
#
# Este script corre ANTES de arrancar FastAPI.
# Su trabajo: asegurarse de que la base de datos esté lista
# y las migraciones aplicadas antes de aceptar requests.
#
# set -e → si cualquier comando falla, el script para inmediatamente
# Esto evita que FastAPI arranque con una DB en mal estado
set -e

echo "🔄 Esperando a que PostgreSQL esté disponible..."

# Esperar a que la DB acepte conexiones
# pg_isready verifica si PostgreSQL está listo para aceptar conexiones
# -h db → el hostname del servicio de base de datos en docker-compose
# Reintenta cada segundo hasta que responda
until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(os.environ['DATABASE_URL'])
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "   PostgreSQL no disponible aún, reintentando..."
    sleep 1
done

echo "✅ PostgreSQL listo"

echo "🔄 Aplicando migraciones de base de datos..."
alembic upgrade head
echo "✅ Migraciones aplicadas"

echo "🚀 Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
