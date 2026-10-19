"""Instala e inicia MariaDB compatible localmente, separado de XAMPP."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import zipfile

import pymysql
import requests

ROOT = Path(__file__).resolve().parents[1]
VERSION = "10.11.19"
TOOLS = ROOT / "reports" / "mariadb-local"
BASE = TOOLS / f"mariadb-{VERSION}-winx64"
DATA = TOOLS / "data"
CONFIG = TOOLS / "my.ini"
PORT = 3307


def download() -> None:
    TOOLS.mkdir(parents=True, exist_ok=True)
    filename = f"mariadb-{VERSION}-winx64.zip"
    archive = TOOLS / filename
    source = f"https://dlm.mariadb.com/4800088/MariaDB/mariadb-{VERSION}/winx64-packages/{filename}"
    checksums_url = f"https://archive.mariadb.org/mariadb-{VERSION}/winx64-packages/sha256sums.txt"
    response = requests.get(checksums_url, timeout=60)
    response.raise_for_status()
    checksums = response.text
    expected = next(line.split()[0] for line in checksums.splitlines()
                    if line.split() and filename == line.split()[-1].lstrip("./*"))
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        with requests.get(source, stream=True, timeout=(30, 120)) as response:
            response.raise_for_status()
            with archive.open("wb") as output:
                downloaded = 0
                for chunk in response.iter_content(1024 * 1024):
                    output.write(chunk)
                    downloaded += len(chunk)
                    if downloaded % (10 * 1024 * 1024) == 0:
                        print(f"Descargados {downloaded // (1024 * 1024)} MiB", flush=True)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError("El SHA256 no coincide con el publicado por MariaDB")
    if not (BASE / "bin" / "mariadbd.exe").exists():
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                (TOOLS / member.filename).resolve().relative_to(TOOLS.resolve())
            bundle.extractall(TOOLS)
    (TOOLS / "source.json").write_text(json.dumps(
        {"version": VERSION, "source": source, "checksums": checksums_url, "sha256": actual}, indent=2), encoding="utf-8")
    print(f"MariaDB {VERSION} descargado y SHA256 verificado.", flush=True)


def initialize() -> None:
    if (DATA / "mysql").exists():
        print("Directorio de datos existente; se conserva.")
    else:
        subprocess.run([str(BASE / "bin" / "mariadb-install-db.exe"),
                        f"--datadir={DATA}", f"--port={PORT}"], cwd=BASE, check=True, timeout=120)
    CONFIG.write_text(
        f"[mysqld]\nbasedir={BASE.as_posix()}\ndatadir={DATA.as_posix()}\n"
        f"port={PORT}\nbind-address=127.0.0.1\ncharacter-set-server=utf8mb4\n"
        "collation-server=utf8mb4_unicode_ci\ndefault-time-zone=+00:00\n"
        "innodb-buffer-pool-size=128M\nmax-allowed-packet=64M\n"
        f"log-error={TOOLS.as_posix()}/server-error.log\n", encoding="utf-8")
    print("Instancia local inicializada.", flush=True)


def connect():
    return pymysql.connect(host="127.0.0.1", port=PORT, user="root", password="", connect_timeout=2)


def start() -> None:
    try:
        with connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION(), @@datadir")
                version, directory = cursor.fetchone()
                if not version.startswith(VERSION) or Path(directory).resolve() != DATA.resolve():
                    raise RuntimeError("El puerto 3307 pertenece a otra instancia")
                print("La instancia compatible ya esta iniciada.")
                return
    except pymysql.OperationalError as error:
        if error.args[0] not in (2003, 2002):
            raise
    with (TOOLS / "server-console.log").open("a", encoding="utf-8") as log:
        server = subprocess.Popen([str(BASE / "bin" / "mariadbd.exe"), f"--defaults-file={CONFIG}", "--console"],
                                  cwd=BASE, stdout=log, stderr=subprocess.STDOUT,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
    (TOOLS / "server.pid").write_text(str(server.pid), encoding="ascii")
    for _ in range(120):
        if server.poll() is not None:
            raise RuntimeError("MariaDB no inicio; revisar reports/mariadb-local/server-error.log")
        try:
            with connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    print(f"MariaDB {cursor.fetchone()[0]} disponible en 127.0.0.1:{PORT}", flush=True)
                    return
        except pymysql.OperationalError:
            time.sleep(0.5)
    raise TimeoutError("MariaDB no estuvo listo en 60 segundos")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "start"])
    arguments = parser.parse_args()
    if arguments.action == "install":
        download()
        initialize()
    start()
