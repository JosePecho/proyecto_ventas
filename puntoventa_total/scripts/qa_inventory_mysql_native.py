"""MySQL real desechable sin Docker; no utiliza servicios ni datos existentes.

Uso: python scripts/qa_inventory_mysql_native.py --basedir RUTA_MYSQL [--full]
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time

import pymysql


def cargar_zonas(cursor):
    # Las consultas de esta suite usan UTC y America/Lima en fechas actuales.
    # La instancia es desechable: no se instala una tabla historica productiva.
    for nombre, desplazamiento in (("UTC", 0), ("America/Lima", -18000)):
        cursor.execute("INSERT INTO mysql.time_zone (Use_leap_seconds) VALUES ('N')")
        identificador = cursor.lastrowid
        cursor.execute("INSERT INTO mysql.time_zone_name (Name, Time_zone_id) VALUES (%s, %s)",
                       (nombre, identificador))
        cursor.execute("INSERT INTO mysql.time_zone_transition_type "
                       "(Time_zone_id, Transition_type_id, `Offset`, Is_DST, Abbreviation) "
                       "VALUES (%s, 0, %s, 0, %s)", (identificador, desplazamiento, "UTC" if nombre == "UTC" else "-05"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--basedir", type=Path, required=True)
    parser.add_argument("--full", action="store_true", help="Ejecutar los cuatro niveles, no solo integracion")
    parser.add_argument("--target", action="append", help="Directorio o archivo pytest; puede repetirse")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--report-prefix", default="inventory-mysql-native")
    args = parser.parse_args()
    if not args.report_prefix.replace("-", "").replace("_", "").isalnum():
        parser.error("--report-prefix solo admite letras, numeros, guion y guion bajo")
    basedir = args.basedir.resolve()
    binary = basedir / "bin" / ("mysqld.exe" if os.name == "nt" else "mysqld")
    if not binary.is_file():
        parser.error("No se encontro bin/mysqld en --basedir")
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    database = "qa_inventory_" + secrets.token_hex(6)
    password = secrets.token_urlsafe(32)
    with socket.socket() as reservado:
        reservado.bind(("127.0.0.1", 0))
        port = reservado.getsockname()[1]
    temporary_root = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix="qa-inventory-mysql-", dir=temporary_root) as temporary:
        Path(temporary).resolve().relative_to(temporary_root)
        datadir = Path(temporary) / "data"
        common = [str(binary), "--no-defaults", f"--basedir={basedir}", f"--datadir={datadir}"]
        with (reports / "mysql-native-init.log").open("w", encoding="utf-8") as log:
            subprocess.run([*common, "--initialize-insecure", "--console"], stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=120)
        with (reports / "mysql-native-server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen([*common, *(["--no-monitor"] if os.name == "nt" else []), "--console", "--bind-address=127.0.0.1",
                f"--port={port}", "--mysqlx=0", "--skip-log-bin", "--innodb-buffer-pool-size=64M",
                "--default-time-zone=+00:00"], stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                deadline = time.monotonic() + 90
                while True:
                    if server.poll() is not None:
                        raise RuntimeError("MySQL no pudo iniciar; consulte reports/mysql-native-server.log")
                    try:
                        db = pymysql.connect(host="127.0.0.1", port=port, user="root", password="",
                                             connect_timeout=2, autocommit=True)
                        break
                    except pymysql.OperationalError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError("MySQL no estuvo disponible en 90 segundos")
                        time.sleep(0.25)
                with db:
                    with db.cursor() as cursor:
                        cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (password,))
                        cursor.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4")
                        cargar_zonas(cursor)
                        cursor.execute("SELECT VERSION(), @@default_storage_engine, "
                                       "CONVERT_TZ('2026-10-16 12:00:00', 'UTC', 'America/Lima')")
                        version, engine, converted = cursor.fetchone()
                        assert engine == "InnoDB" and str(converted) == "2026-10-16 07:00:00"
                env = dict(os.environ, DJANGO_SETTINGS_MODULE="config.settings.testing_mysql",
                    INVENTORY_EPHEMERAL_MYSQL="1", QA_MYSQL_DATABASE=database, QA_MYSQL_USER="root",
                    QA_MYSQL_PASSWORD=password, QA_MYSQL_HOST="127.0.0.1", QA_MYSQL_PORT=str(port),
                    QA_REQUIRE_BROWSER="1")
                targets = args.target or ([] if args.full else ["tests/integration/test_inventario_requisitos.py",
                                              "tests/integration/test_inventario_mysql.py"]
                )
                coverage_args = (["--cov=src", "--cov-fail-under=80",
                    f"--cov-report=json:reports/{args.report_prefix}-coverage.json",
                    f"--cov-report=xml:reports/{args.report_prefix}-coverage.xml"] if args.coverage else [])
                result = subprocess.run([sys.executable, "-m", "pytest", *targets, "--reuse-db",
                    "-q", "-p", "no:cacheprovider", f"--junitxml=reports/{args.report_prefix}.xml", *coverage_args],
                    cwd=root, env=env)
                evidence = dict(engine=engine, version=version, ephemeral=True, container=False,
                                full=bool(args.full and not args.target), exit_code=result.returncode,
                                executed_at=datetime.now(timezone.utc).isoformat(),
                                timezone_fixture="UTC y America/Lima, fechas actuales")
                (reports / f"{args.report_prefix}.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
                print(json.dumps(evidence))
                return result.returncode
            finally:
                try:
                    with pymysql.connect(host="127.0.0.1", port=port, user="root", password=password,
                                         connect_timeout=2, autocommit=True) as shutdown:
                        with shutdown.cursor() as cursor:
                            cursor.execute("SHUTDOWN")
                except pymysql.MySQLError:
                    server.terminate()
                try:
                    server.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
