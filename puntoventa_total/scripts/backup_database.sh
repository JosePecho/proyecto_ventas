#!/usr/bin/env bash
# Backup completo de MySQL con rotacion simple por fecha.
set -euo pipefail

: "${DB_NAME:=puntoventa}"
: "${DB_USER:=puntoventa}"
: "${DB_PASSWORD:=puntoventa_secret}"
: "${DB_HOST:=localhost}"
: "${DB_PORT:=3306}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
FECHA="$(date +%Y%m%d_%H%M%S)"
ARCHIVO="$BACKUP_DIR/${DB_NAME}_${FECHA}.sql.gz"

mkdir -p "$BACKUP_DIR"

mysqldump \
  --host="$DB_HOST" --port="$DB_PORT" \
  --user="$DB_USER" --password="$DB_PASSWORD" \
  --single-transaction --routines --triggers \
  "$DB_NAME" | gzip > "$ARCHIVO"

echo "[ok] backup generado: $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"

# conserva los ultimos 30 backups
ls -1t "$BACKUP_DIR"/${DB_NAME}_*.sql.gz | tail -n +31 | xargs -r rm --
echo "[ok] rotacion aplicada (se conservan 30 backups)"

