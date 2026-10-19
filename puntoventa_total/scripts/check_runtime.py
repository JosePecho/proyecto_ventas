"""Comprueba el entorno configurado sin cambiar datos ni mostrar credenciales."""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")


def main():
    import django
    django.setup()
    from django.conf import settings
    from django.core.cache import cache
    from django.core.checks import run_checks, ERROR
    from django.contrib.staticfiles import finders
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    checks = {}
    errores = [error.id for error in run_checks() if error.level >= ERROR]
    checks["django"] = {"ok": not errores, "errores": errores}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
        checks["database"] = {"ok": True, "engine": connection.vendor}
        executor = MigrationExecutor(connection)
        pendientes = [f"{m.app_label}.{m.name}" for m, _ in executor.migration_plan(executor.loader.graph.leaf_nodes())]
        checks["migrations"] = {"ok": not pendientes, "pendientes": pendientes}
    except Exception as exc:
        checks["database"] = {
            "ok": False, "error": type(exc).__name__,
            "error_code": exc.args[0] if exc.args and isinstance(exc.args[0], int) else None,
            "host_local": connection.settings_dict["HOST"] in ("localhost", "127.0.0.1", "::1"),
            "host_docker": connection.settings_dict["HOST"] == "db",
        }
    finally:
        connection.close()
    clave = f"runtime-check-{uuid4().hex}"
    try:
        cache.set(clave, "ok", timeout=10)
        checks["cache"] = {"ok": cache.get(clave) == "ok"}
        cache.delete(clave)
    except Exception as exc:
        checks["cache"] = {"ok": False, "error": type(exc).__name__}
    archivos = ["css/base.css", "js/main.js", "js/pos/carrito.js", "images/logo.svg"]
    faltantes = [nombre for nombre in archivos if not finders.find(nombre)]
    checks["static"] = {"ok": not faltantes, "faltantes": faltantes}
    resultado = {"settings": settings.SETTINGS_MODULE, "checks": checks, "ok": all(c["ok"] for c in checks.values())}
    print(json.dumps(resultado, indent=2))
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
