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

# base de datos
if python manage.py check --database default > /dev/null 2>&1; then
  echo "[ok] base de datos accesible"
else
  echo "[FALLA] base de datos inaccesible"
  FALLAS=$((FALLAS + 1))
fi

# redis / celery
if python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development'); django.setup(); from django.core.cache import cache; cache.set('health','1',5); assert cache.get('health')=='1'" > /dev/null 2>&1; then
  echo "[ok] cache Redis operativa"
else
  echo "[ADVERTENCIA] cache no disponible (se usara locmem en desarrollo)"
fi

exit "$FALLAS"

