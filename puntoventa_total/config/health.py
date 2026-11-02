"""Readiness real: no expone nombres de servicios, excepciones ni credenciales."""
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe


@require_safe
def healthz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone()[0] != 1:
                raise RuntimeError("Database unavailable")
        cache.get("puntoventa-readiness-probe")
    except Exception:
        respuesta = JsonResponse({"status": "unavailable"}, status=503)
    else:
        respuesta = JsonResponse({"status": "ok"})
    respuesta["Cache-Control"] = "no-store"
    return respuesta
