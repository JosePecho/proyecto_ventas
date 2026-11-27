"""Ejecuta pruebas Google en un esquema nuevo y aislado del MariaDB local."""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import environ
import pymysql

ROOT = Path(__file__).resolve().parents[1]


def main():
    environ.Env.read_env(ROOT / ".env")
    nombre = "qa_google_" + uuid4().hex[:16]
    if nombre == os.environ["DB_NAME"] or not nombre.startswith("qa_google_"):
        raise RuntimeError("Destino no aislado")
    opciones = {"host": os.environ.get("DB_HOST", "127.0.0.1"), "port": int(os.environ.get("DB_PORT", "3306")),
                "user": os.environ["DB_USER"], "password": os.environ.get("DB_PASSWORD", ""), "autocommit": True}
    with pymysql.connect(**opciones) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE `{nombre}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        entorno = dict(os.environ)
        entorno.update(DJANGO_SETTINGS_MODULE="config.settings.testing_mysql", INVENTORY_EPHEMERAL_MYSQL="1",
            QA_MYSQL_DATABASE=nombre, QA_MYSQL_HOST=opciones["host"], QA_MYSQL_PORT=str(opciones["port"]),
            QA_MYSQL_USER=opciones["user"], QA_MYSQL_PASSWORD=opciones["password"])
        codigo = subprocess.run([sys.executable, "-m", "pytest", "tests/integration/test_google_login.py",
            "tests/integration/test_google_registro_concurrencia.py",
            "--reuse-db", "-q", "-p", "no:cacheprovider", "--junitxml=reports/google-registro-mysql.xml"],
            cwd=ROOT, env=entorno).returncode
        if codigo == 0:
            with conexion.cursor() as cursor:
                cursor.execute(f"DROP DATABASE `{nombre}`")
            print("Esquema QA eliminado tras aprobar las pruebas. Base original intacta.")
        else:
            print("Pruebas fallidas: se conserva el esquema QA para diagnóstico.")
        return codigo


if __name__ == "__main__":
    raise SystemExit(main())
