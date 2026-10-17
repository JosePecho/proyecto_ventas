"""Conserva métricas por perfil y verifica evidencias reales de los cuatro niveles."""
import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def perfil(nombre):
    prefix = f"rf030-050-{nombre}"
    root = ET.parse(REPORTS / f"{prefix}.xml").getroot()
    suites = list(root.iter("testsuite"))
    conteos = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    if not conteos["tests"] or any(conteos[k] for k in ("failures", "errors", "skipped")):
        raise ValueError(f"{nombre}: suite incompleta o fallida: {conteos}")
    cobertura = json.loads((REPORTS / f"{prefix}-coverage.json").read_text())["totals"]["percent_covered"]
    if cobertura < 80:
        raise ValueError(f"{nombre}: cobertura {cobertura} inferior a 80")
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
        metrics = json.loads((REPORTS / f"{prefix}-k6-{tipo}.json").read_text())["metrics"]
        checks = metrics["checks"]["value"]
        p95 = metrics["http_req_duration"]["p(95)"]
        if checks != 1 or metrics["http_req_failed"]["value"] != 0 or p95 >= 500:
            raise ValueError(f"{nombre}: presupuesto k6 {tipo} incumplido")
        cargas[tipo] = {"checks": checks, "http_p95_ms": round(p95, 2)}
        if tipo == "pos":
            cobro = metrics["tiempo_cobro_ms"]["p(95)"]
            if cobro >= 100 or metrics["tiempo_busqueda_ms"]["p(95)"] >= 200:
                raise ValueError(f"{nombre}: presupuesto de cobro/búsqueda incumplido")
            cargas[tipo]["cobro_p95_ms"] = round(cobro, 2)
    return dict(conteos, coverage=round(cobertura, 2), niveles=niveles, k6=cargas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", choices=("production", "qa"))
    args = parser.parse_args()
    if args.capture:
        for tipo in ("pos", "pedidos", "reportes"):
            shutil.copyfile(REPORTS / f"k6-{tipo}-summary.json", REPORTS / f"rf030-050-{args.capture}-k6-{tipo}.json")
        resultado = {args.capture: perfil(args.capture)}
    else:
        resultado = {nombre: perfil(nombre) for nombre in ("production", "qa")}
        (REPORTS / "rf030-050-final-evidence.json").write_text(json.dumps(resultado, indent=2), encoding="utf-8")
    print(json.dumps(resultado, indent=2))


if __name__ == "__main__":
    main()
