"""Crea MySQL efimero y ejecuta pytest. Sin Docker/dependencias termina con 2."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit


def main():
    docker = shutil.which("docker")
    if docker is None:
        print("Falta Docker CLI/Desktop. Instale e inicie Docker; este nivel NO se ejecuto.")
        return 2
    if subprocess.run([docker, "info"], capture_output=True).returncode:
        print("Docker Engine no responde. Este nivel NO se ejecuto.")
        return 2
    if importlib.util.find_spec("testcontainers") is None:
        print("Instale requirements/qa-inventory-mysql.txt. Este nivel NO se ejecuto.")
        return 2
    from testcontainers.mysql import MySqlContainer

    root = Path(__file__).resolve().parents[1]
    image = os.environ.get("INVENTORY_MYSQL_IMAGE", "mysql:8.4.3")
    with MySqlContainer(image, dialect="pymysql") as mysql:
        url = urlsplit(mysql.get_connection_url())
        env = dict(os.environ)
        env.update(
            DJANGO_SETTINGS_MODULE="config.settings.testing_mysql",
            INVENTORY_EPHEMERAL_MYSQL="1",
            QA_MYSQL_DATABASE=url.path.lstrip("/"),
            QA_MYSQL_USER=unquote(url.username),
            QA_MYSQL_PASSWORD=unquote(url.password),
            # En Linux mysqlclient interpreta localhost como socket Unix y
            # omite el puerto publicado por Docker. Forzar TCP para loopback.
            QA_MYSQL_HOST="127.0.0.1" if url.hostname == "localhost" else url.hostname,
            QA_MYSQL_PORT=str(url.port),
        )
        targets = sys.argv[1:] or [
            "tests/integration/test_inventario_requisitos.py",
            "tests/integration/test_inventario_mysql.py",
        ]
        command = [sys.executable, "-m", "pytest", *targets, "--reuse-db", "-q", "-p", "no:cacheprovider"]
        return subprocess.run(command, cwd=root, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
