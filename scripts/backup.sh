#!/bin/bash
# ============================================================
# scripts/backup.sh — Backup de PostgreSQL
# ============================================================
#
# Crea un dump comprimido de la base de datos con timestamp.
# En producción esto debería correr en un cron job diario.
#
# Cron job recomendado (en el VPS, correr: crontab -e):
#   0 3 * * * /opt/ferreteria-saas/scripts/backup.sh >> /var/log/backup.log 2>&1
#   Esto corre el backup todos los días a las 3am.
# ============================================================

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="backup_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "🗃️  Creando backup: $FILENAME"

# pg_dump dentro del contenedor, comprimido con gzip
docker compose exec -T db pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    | gzip > "$BACKUP_DIR/$FILENAME"

echo "✅ Backup guardado en $BACKUP_DIR/$FILENAME"

# Mantener solo los últimos 7 backups
echo "🧹 Limpiando backups antiguos (mantiene últimos 7)..."
ls -t "$BACKUP_DIR"/backup_*.sql.gz | tail -n +8 | xargs -r rm

echo "📦 Backups actuales:"
ls -lh "$BACKUP_DIR"/
