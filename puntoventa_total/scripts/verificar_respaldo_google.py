"""Respaldo previo a migración, restauración aislada y comparación sin datos en logs."""
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import environ
import pymysql

ROOT = Path(__file__).resolve().parents[1]
environ.Env.read_env(ROOT / ".env")


def huella(conexion):
    resultado = {}
    with conexion.cursor() as cursor:
        cursor.execute("SHOW FULL TABLES")
        tablas = cursor.fetchall()
        if any(tipo != "BASE TABLE" for _, tipo in tablas):
            raise RuntimeError("Se requiere revisar vistas antes de continuar")
        for tabla, _ in tablas:
            identificador = "`" + tabla.replace("`", "``") + "`"
            cursor.execute(f"SHOW CREATE TABLE {identificador}")
            esquema = cursor.fetchone()[1]
            cursor.execute(f"SELECT * FROM {identificador}")
            filas = sorted(hashlib.sha256(json.dumps(fila, default=str, ensure_ascii=True).encode()).hexdigest()
                           for fila in cursor.fetchall())
            resultado[tabla] = {"filas": len(filas), "sha256": hashlib.sha256("".join(filas).encode()).hexdigest(),
                                "esquema": esquema}
    return resultado


def main():
    directorio = Path(os.environ["USERPROFILE"]) / ".puntoventa-backups" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    directorio.mkdir(parents=True, exist_ok=False)
    usuario_windows = os.environ["USERDOMAIN"] + "\\" + os.environ["USERNAME"]
    subprocess.run(["icacls", str(directorio), "/inheritance:r", "/grant:r",
                    f"{usuario_windows}:(OI)(CI)F", "SYSTEM:(OI)(CI)F"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    nombre = os.environ["DB_NAME"]
    temporal = "qa_restore_google_" + uuid4().hex[:16]
    if nombre == temporal or not temporal.startswith("qa_restore_google_"):
        raise RuntimeError("Destino temporal inválido")
    opciones = {"host": os.environ.get("DB_HOST", "127.0.0.1"), "port": int(os.environ.get("DB_PORT", "3306")),
                "user": os.environ["DB_USER"], "password": os.environ.get("DB_PASSWORD", ""),
                "charset": "utf8mb4", "autocommit": True}
    binarios = ROOT / "reports/mariadb-local/mariadb-10.11.19-winx64/bin"
    config = directorio / "conexion.cnf"
    def escapar(valor):
        return str(valor).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
    config.write_text("[client]\n" + "".join(f'{k}="{escapar(v)}"\n' for k, v in
        {"host": opciones["host"], "port": opciones["port"], "user": opciones["user"],
         "password": opciones["password"], "default-character-set": "utf8mb4"}.items()), encoding="utf-8")
    archivo = directorio / "puntoventa-completo.sql"
    conexion = pymysql.connect(**opciones, database=nombre)
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s", (nombre,))
            if cursor.fetchone()[0] != 28:
                raise RuntimeError("La base original no contiene las 28 tablas esperadas")
            cursor.execute("FLUSH TABLES WITH READ LOCK")
        try:
            with archivo.open("wb") as salida:
                subprocess.run([str(binarios / "mariadb-dump.exe"), f"--defaults-extra-file={config}",
                    "--single-transaction", "--skip-lock-tables", "--routines", "--triggers", "--events",
                    "--hex-blob", "--no-tablespaces", nombre], stdout=salida, stderr=subprocess.PIPE, check=True)
            original = huella(conexion)
        finally:
            with conexion.cursor() as cursor:
                cursor.execute("UNLOCK TABLES")
        with conexion.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE `{temporal}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("Respaldo creado. Restaurando únicamente en base temporal aislada.", flush=True)
        with archivo.open("rb") as entrada:
            subprocess.run([str(binarios / "mariadb.exe"), f"--defaults-extra-file={config}",
                f"--database={temporal}"], stdin=entrada, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        with pymysql.connect(**opciones, database=temporal) as restaurada:
            copia = huella(restaurada)
        if original != copia or len(copia) != 28:
            raise RuntimeError("La restauración no coincide; se conserva la base temporal")
        # Solo se elimina el destino generado después de comparar todos los esquemas y registros.
        with conexion.cursor() as cursor:
            cursor.execute(f"DROP DATABASE `{temporal}`")
        manifiesto = {"validado": True, "fecha_utc": datetime.now(UTC).isoformat(), "tablas": len(original),
            "registros": sum(t["filas"] for t in original.values()),
            "archivo_sha256": hashlib.sha256(archivo.read_bytes()).hexdigest(), "verificacion": original,
            "temporal_eliminada": True}
        (directorio / "verificacion.json").write_text(json.dumps(manifiesto, indent=2), encoding="utf-8")
        print(f"Respaldo válido: {archivo}")
        print(f"28/28 tablas y {manifiesto['registros']} registros verificados por SHA256 y esquema.")
        print("Base temporal eliminada después de verificar. Base original conservada.")
        return 0
    finally:
        conexion.close()
        config.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"DETENIDO: verificación fallida ({type(exc).__name__}). No aplicar migraciones.")
        sys.exit(1)
