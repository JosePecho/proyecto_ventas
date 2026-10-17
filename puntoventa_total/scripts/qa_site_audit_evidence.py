"""Captura la suite completa y k6 por perfil antes de ejecutar el siguiente."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def fingerprint():
    archivos = []
    for carpeta in ("src", "config", "templates", "static", "tests", "requirements", "deployment"):
        archivos.extend(p for p in (ROOT / carpeta).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    archivos.extend(ROOT / nombre for nombre in ("Dockerfile", "docker-compose.yml", "docker-compose.local.yml", "docker-compose.https.yml", "pyproject.toml"))
    contenido = "\n".join(f"{p.relative_to(ROOT).as_posix()}:{hashlib.sha256(p.read_bytes()).hexdigest()}"
                           for p in sorted(archivos))
    return hashlib.sha256(contenido.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, choices=("qa", "production"))
    args = parser.parse_args()
    prefijo = "site-final-" + args.capture
    suite = ET.parse(REPORTS / f"{prefijo}.xml").getroot()
    casos = list(suite.iter("testcase"))
    fallidos = sum(c.find("failure") is not None or c.find("error") is not None for c in casos)
    omitidos = sum(c.find("skipped") is not None for c in casos)
    niveles = {}
    for caso in casos:
        clase = caso.get("classname", "")
        nivel = next((n for n in ("unit", "integration", "uat") if f".{n}." in f".{clase}."), "system")
        niveles[nivel] = niveles.get(nivel, 0) + 1
    ejecucion = json.loads((REPORTS / f"{prefijo}.json").read_text())
    cobertura = json.loads((REPORTS / f"{prefijo}-coverage.json").read_text())["totals"]["percent_covered"]
    snapshots = {}
    for nombre in ("k6-pos-summary.json", "k6-server.json", "redis-real.json"):
        origen = REPORTS / nombre
        destino = REPORTS / f"{prefijo}-{nombre}"
        destino.write_bytes(origen.read_bytes())
        snapshots[nombre] = str(destino.relative_to(ROOT))
    k6 = json.loads((REPORTS / f"{prefijo}-k6-pos-summary.json").read_text())
    cobro = k6["metrics"]["tiempo_cobro_ms"]["p(95)"]
    paquetes = {}
    for paquete in ("Django", "djangorestframework", "Pillow", "cryptography", "mysqlclient", "celery", "redis", "sentry-sdk", "waitress"):
        try:
            paquetes[paquete] = version(paquete)
        except PackageNotFoundError:
            paquetes[paquete] = None
    resultado = {
        "profile": args.capture, "captured_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0], "django": version("Django"),
        "packages": paquetes,
        "source_sha256": fingerprint(), "tests": len(casos), "failed": fallidos,
        "skipped": omitidos, "levels": niveles, "coverage": cobertura,
        "payment_p95_ms": cobro, "execution": ejecucion, "artifacts": snapshots,
        "ok": bool(casos) and not fallidos and not omitidos and ejecucion["exit_code"] == 0
              and cobertura >= 80 and cobro < 100,
    }
    (REPORTS / f"{prefijo}-evidence.json").write_text(json.dumps(resultado, indent=2), encoding="utf-8")
    print(json.dumps(resultado, indent=2))
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
