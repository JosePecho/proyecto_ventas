#!/usr/bin/env bash
# Verifica que los servicios criticos respondan (para monitoreo o smoke tests).
set -uo pipefail

URL_BASE="${URL_BASE:-http://localhost:8000}"
FALLAS=0

verificar() {
  local nombre="$1" url="$2"
  if curl -fsS --max-time 5 "$url" > /dev/null 2>&1; then
    echo "[ok] $nombre responde"
  else
    echo "[FALLA] $nombre no responde ($url)"
    FALLAS=$((FALLAS + 1))
  fi
}

verificar "Web (healthz)" "$URL_BASE/healthz"
verificar "Catalogo"      "$URL_BASE/catalogo/"

# Configuracion, conexion SQL real, migraciones pendientes y cache configurada.
if python scripts/check_runtime.py > /dev/null 2>&1; then
  echo "[ok] entorno de la aplicacion operativo"
else
  echo "[FALLA] ejecutar python scripts/check_runtime.py para diagnosticar"
  FALLAS=$((FALLAS + 1))
fi

exit "$FALLAS"

