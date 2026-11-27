"""Aplica solo identity.0002 después de comprobar respaldo y conservación de datos."""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")


def main():
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from verificar_respaldo_google import huella

    directorio = Path(sys.argv[1]).resolve()
    permitido = (Path(os.environ["USERPROFILE"]) / ".puntoventa-backups").resolve()
    directorio.relative_to(permitido)
    manifiesto = json.loads((directorio / "verificacion.json").read_text(encoding="utf-8"))
    if (not manifiesto.get("validado") or manifiesto.get("tablas") != 28
            or hashlib.sha256((directorio / "puntoventa-completo.sql").read_bytes()).hexdigest() != manifiesto["archivo_sha256"]):
        raise RuntimeError("El respaldo no supera la validación")
    plan = MigrationExecutor(connection).migration_plan([("identity", "0002_googlevinculomodel")])
    if [(m.app_label, m.name, inversa) for m, inversa in plan] != [("identity", "0002_googlevinculomodel", False)]:
        raise RuntimeError("El plan contiene migraciones inesperadas o ya se aplicó")
    # La API nativa del backend usa el mismo cursor DB-API que la verificación del dump.
    connection.ensure_connection()
    antes = huella(connection.connection)
    if len(antes) != 28:
        raise RuntimeError("Número de tablas original inesperado")
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM django_migrations")
        historial = set(cursor.fetchall())
        cursor.execute("SELECT id, app_label, model FROM django_content_type")
        tipos_antes = set(cursor.fetchall())
        cursor.execute("SELECT id, name, content_type_id, codename FROM auth_permission")
        permisos_antes = set(cursor.fetchall())
    call_command("migrate", "identity", "0002", interactive=False, verbosity=1)
    despues = huella(connection.connection)
    nueva = despues.pop("identity_google_vinculo")
    if len(despues) != 28 or nueva["filas"] != 0:
        raise RuntimeError("Esquema final inesperado")
    for tabla in antes:
        if tabla not in {"django_migrations", "django_content_type", "auth_permission"} and antes[tabla] != despues[tabla]:
            raise RuntimeError("Se detectó un cambio en datos previos: detener y revisar")
        if tabla in {"django_migrations", "django_content_type", "auth_permission"}:
            esquemas = [re.sub(r"AUTO_INCREMENT=\d+", "AUTO_INCREMENT=N", d[tabla]["esquema"]) for d in (antes, despues)]
            if esquemas[0] != esquemas[1]:
                raise RuntimeError("Cambio inesperado en esquema técnico")
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM django_migrations")
        final = set(cursor.fetchall())
        cursor.execute("SELECT id, app_label, model FROM django_content_type")
        tipos_despues = set(cursor.fetchall())
        cursor.execute("SELECT id, name, content_type_id, codename FROM auth_permission")
        permisos_despues = set(cursor.fetchall())
    if not historial.issubset(final) or len(final - historial) != 1:
        raise RuntimeError("El historial de migraciones no coincide")
    tipos_nuevos = tipos_despues - tipos_antes
    if (not tipos_antes.issubset(tipos_despues) or len(tipos_nuevos) != 1
            or next(iter(tipos_nuevos))[1:] != ("identity", "googlevinculomodel")):
        raise RuntimeError("Cambio inesperado en tipos de contenido")
    tipo_nuevo_id = next(iter(tipos_nuevos))[0]
    permisos_nuevos = permisos_despues - permisos_antes
    if (not permisos_antes.issubset(permisos_despues) or len(permisos_nuevos) != 4
            or any(fila[2] != tipo_nuevo_id for fila in permisos_nuevos)
            or {fila[3] for fila in permisos_nuevos} != {
                accion + "_googlevinculomodel" for accion in ("add", "change", "delete", "view")}):
        raise RuntimeError("Cambio inesperado en permisos técnicos")
    resumen = {"migracion": "identity.0002_googlevinculomodel", "tablas_antes": 28, "tablas_despues": 29,
               "datos_previos_conservados": True, "vinculaciones_creadas": 0}
    (directorio / "migracion_google_verificada.json").write_text(json.dumps(resumen, indent=2), encoding="utf-8")
    print("Migración verificada: 28 tablas originales conservadas y 1 tabla nueva vacía. Sin vinculaciones automáticas.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"DETENIDO: comprobación de migración fallida ({type(exc).__name__}). Revisar antes de continuar.")
        raise SystemExit(1) from None
