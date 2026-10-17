"""Conserva métricas por perfil y verifica evidencias reales de los cuatro niveles."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def huella_archivo(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def huella_codigo():
    huella = hashlib.sha256()
    for carpeta in ("src", "config", "tests", "requirements"):
        for path in sorted((ROOT / carpeta).rglob("*")):
            if path.suffix in (".py", ".txt", ".js", ".feature"):
                huella.update(path.relative_to(ROOT).as_posix().encode())
                huella.update(path.read_bytes())
    return huella.hexdigest()


def artefactos(prefix):
    return [REPORTS / f"{prefix}.xml", REPORTS / f"{prefix}-coverage.json",
            *[REPORTS / f"{prefix}-k6-{tipo}.json" for tipo in ("pos", "pedidos", "reportes")]]


def perfil(nombre):
    prefix = f"rf030-050-{nombre}"
    procedencia = json.loads((REPORTS / f"{prefix}-provenance.json").read_text(encoding="utf-8"))
    if procedencia["code_sha256"] != huella_codigo():
        raise ValueError(f"{nombre}: el código cambió desde la captura; ejecutar de nuevo")
    for path in artefactos(prefix):
        if huella_archivo(path) != procedencia["artifacts_sha256"][path.name]:
            raise ValueError(f"{nombre}: artefacto modificado desde la captura: {path.name}")
    root = ET.parse(REPORTS / f"{prefix}.xml").getroot()
    suites = list(root.iter("testsuite"))
    conteos = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    problemas = []
    if not conteos["tests"] or any(conteos[k] for k in ("failures", "errors", "skipped")):
        problemas.append(f"Suite incompleta o fallida: {conteos}")
    cobertura = json.loads((REPORTS / f"{prefix}-coverage.json").read_text())["totals"]["percent_covered"]
    if cobertura < 80:
        problemas.append(f"Cobertura {cobertura} inferior a 80")
    niveles = dict(unit=0, integration=0, system=0, uat=0)
    for caso in root.iter("testcase"):
        classname = caso.get("classname", "")
        for nivel, carpetas in {"unit": ("tests.unit",), "integration": ("tests.integration",),
                "system": ("tests.system", "tests.e2e", "tests.functional", "tests.performance"),
                "uat": ("tests.uat",)}.items():
            if any(classname.startswith(carpeta) for carpeta in carpetas):
                niveles[nivel] += 1
    if not all(niveles.values()) or sum(niveles.values()) != conteos["tests"]:
        raise ValueError(f"{nombre}: faltan niveles o casos sin clasificar: {niveles}")
    cargas = {}
    for tipo in ("pos", "pedidos", "reportes"):
        if not procedencia["k6_same_run"][tipo]:
            cargas[tipo] = {"available": False}
            problemas.append(f"Resumen k6 {tipo} no pertenece a esta ejecución; consultar JUnit")
            continue
        metrics = json.loads((REPORTS / f"{prefix}-k6-{tipo}.json").read_text())["metrics"]
        checks = metrics["checks"]["value"]
        p95 = metrics["http_req_duration"]["p(95)"]
        if checks != 1 or metrics["http_req_failed"]["value"] != 0 or p95 >= 500:
            problemas.append(f"Presupuesto k6 {tipo} incumplido")
        cargas[tipo] = {"available": True, "checks": checks, "http_p95_ms": round(p95, 2)}
        if tipo == "pos":
            cobro = metrics["tiempo_cobro_ms"]["p(95)"]
            if cobro >= 100 or metrics["tiempo_busqueda_ms"]["p(95)"] >= 200:
                problemas.append("Presupuesto de cobro/búsqueda incumplido")
            cargas[tipo]["cobro_p95_ms"] = round(cobro, 2)
    fallos = [f"{caso.get('classname')}.{caso.get('name')}" for caso in root.iter("testcase")
              if caso.find("failure") is not None or caso.find("error") is not None]
    return dict(conteos, coverage=round(cobertura, 2), niveles=niveles, k6=cargas,
                provenance=procedencia, ready=not problemas, problems=problemas, failed_cases=fallos)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", choices=("production", "qa"))
    args = parser.parse_args()
    if args.capture:
        prefix = f"rf030-050-{args.capture}"
        ejecucion = json.loads((REPORTS / f"{prefix}.json").read_text(encoding="utf-8"))
        if not ejecucion["full"]:
            raise ValueError("La captura requiere una ejecución completa")
        fin = datetime.fromisoformat(ejecucion["executed_at"]).timestamp()
        suites = list(ET.parse(REPORTS / f"{prefix}.xml").getroot().iter("testsuite"))
        inicio = min(datetime.fromisoformat(s.get("timestamp")).timestamp()
                     for s in suites)
        misma_ejecucion = {}
        for tipo in ("pos", "pedidos", "reportes"):
            fuente = REPORTS / f"k6-{tipo}-summary.json"
            misma_ejecucion[tipo] = inicio <= fuente.stat().st_mtime <= fin
            shutil.copyfile(fuente, REPORTS / f"{prefix}-k6-{tipo}.json")
        procedencia = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "executed_at": ejecucion["executed_at"],
            "database": {key: ejecucion[key] for key in ("engine", "version", "ephemeral", "container")},
            "python": sys.version.split()[0],
            "k6_same_run": misma_ejecucion,
            "packages": {nombre: version(nombre) for nombre in ("Django", "pytest", "celery", "playwright")},
            "code_sha256": huella_codigo(),
            "artifacts_sha256": {path.name: huella_archivo(path) for path in artefactos(prefix)},
        }
        (REPORTS / f"{prefix}-provenance.json").write_text(json.dumps(procedencia, indent=2), encoding="utf-8")
        resultado = {args.capture: perfil(args.capture)}
    else:
        resultado = {nombre: perfil(nombre) for nombre in ("production", "qa")}
        (REPORTS / "rf030-050-final-evidence.json").write_text(json.dumps(resultado, indent=2), encoding="utf-8")
    print(json.dumps(resultado, indent=2))
    return 0 if all(perfil["ready"] for perfil in resultado.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
