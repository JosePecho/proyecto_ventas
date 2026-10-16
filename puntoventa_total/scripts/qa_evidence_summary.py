"""Comprueba artefactos del CI: sin omisiones, cobertura y presupuesto k6."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    root = Path(__file__).resolve().parents[1]
    run = json.loads((root / "reports/remote-ci.json").read_text(encoding="utf-8"))["runs"][0]
    if run["conclusion"] != "success":
        raise RuntimeError("El CI no esta aprobado")
    evidence = {"run": run["url"], "commit": run["head_sha"], "profiles": {}}
    for artifact in run["artifacts"]:
        directory = Path(artifact["directory"])
        suite = ET.parse(directory / "full-suite.xml").getroot()
        suites = list(suite) if suite.tag == "testsuites" else [suite]
        counts = {name: sum(int(s.attrib.get(name, 0)) for s in suites)
                  for name in ("tests", "failures", "errors", "skipped")}
        coverage = float(ET.parse(directory / "full-coverage.xml").getroot().attrib["line-rate"]) * 100
        metrics = json.loads((directory / "k6-pos-summary.json").read_text())["metrics"]
        result = dict(counts, coverage_pct=round(coverage, 2),
            k6_checks_pct=metrics["checks"]["value"] * 100,
            k6_payment_p95_ms=metrics["tiempo_cobro_ms"]["p(95)"],
            k6_search_p95_ms=metrics["tiempo_busqueda_ms"]["p(95)"])
        if any(counts[k] for k in ("failures", "errors", "skipped")) or not counts["tests"]:
            raise RuntimeError("Hay fallos u omisiones en " + artifact["name"])
        if coverage < 80 or result["k6_checks_pct"] != 100 or result["k6_payment_p95_ms"] >= 100:
            raise RuntimeError("No se cumple el gate en " + artifact["name"])
        evidence["profiles"][artifact["name"]] = result
    if len(evidence["profiles"]) != 2:
        raise RuntimeError("Se requieren ambos perfiles")
    (root / "reports/complete-evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
