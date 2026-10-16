#!/usr/bin/env bash
# Restaura un backup comprimido. Uso: ./scripts/restore_database.sh backups/puntoventa_20260101_100000.sql.gz
set -euo pipefail

: "${DB_NAME:=puntoventa}"
: "${DB_USER:=puntoventa}"
: "${DB_PASSWORD:=puntoventa_secret}"
: "${DB_HOST:=localhost}"
: "${DB_PORT:=3306}"

ARCHIVO="${1:?Indique el archivo .sql.gz a restaurar}"

if [ ! -f "$ARCHIVO" ]; then
  echo "[error] no existe el archivo: $ARCHIVO" >&2
  exit 1
fi

read -r -p "Esto SOBRESCRIBE la base '$DB_NAME'. Continuar? (s/N) " confirmar
if [ "$confirmar" != "s" ]; then
  echo "Abortado."
  exit 0
fi

gunzip -c "$ARCHIVO" | mysql \
  --host="$DB_HOST" --port="$DB_PORT" \
  --user="$DB_USER" --password="$DB_PASSWORD" \
  "$DB_NAME"

echo "[ok] base '$DB_NAME' restaurada desde $ARCHIVO"

