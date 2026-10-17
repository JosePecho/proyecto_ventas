"""Gate de lineas en dominio/aplicacion a partir de cobertura SOLO unitaria."""
import json
from pathlib import Path


def main():
    report = json.loads(Path("reports/audit_unit_coverage.json").read_text(encoding="utf-8"))
    covered = total = 0
    for filename, entry in report["files"].items():
        parts = filename.replace("\\", "/").split("/")
        if "domain" in parts or "application" in parts:
            covered += entry["summary"]["covered_lines"]
            total += entry["summary"]["num_statements"]
    if not total:
        raise SystemExit("No se encontraron lineas de dominio/aplicacion")
    percent = 100 * covered / total
    print(f"Cobertura unitaria dominio/aplicacion: {covered}/{total} = {percent:.2f}% (minimo 80%)")
    return 0 if percent >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
