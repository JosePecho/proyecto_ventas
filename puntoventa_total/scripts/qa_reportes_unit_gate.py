"""Cobertura de núcleo RF-044..050, incluyendo archivos no importados por los tests."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from coverage import Coverage

ROOT = Path(__file__).resolve().parents[1]
ARCHIVOS = [
    "reporting/domain/value_objects/rango_fechas.py",
    "reporting/domain/value_objects/utilidad_historica.py",
    "reporting/application/use_cases/reporte_ventas_diarias.py",
    "reporting/application/use_cases/reporte_ventas_por_fecha.py",
    "reporting/application/use_cases/reporte_productos_mas_vendidos.py",
    "reporting/application/use_cases/reporte_utilidad.py",
    "auditing/domain/entities/registro_auditoria.py",
    "auditing/application/use_cases/consultar_auditoria.py",
    "auditing/application/use_cases/registrar_auditoria.py",
    "auditing/application/use_cases/rastrear_transaccion.py",
    "identity/domain/entities/usuario.py",
    "catalog/domain/entities/categoria.py",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", default="reports/rf044-050-unit.xml")
    parser.add_argument("--data-file", default=".coverage")
    args = parser.parse_args()
    reporte = ET.parse(ROOT / args.junit).getroot()
    casos = list(reporte.iter("testcase"))
    if not casos or any(not c.get("classname", "").startswith("tests.unit.") or
                        any(c.find(tag) is not None for tag in ("failure", "error", "skipped")) for c in casos):
        raise SystemExit("El gate requiere un JUnit unitario aprobado, sin omisiones")
    coverage = Coverage(data_file=str(ROOT / args.data_file))
    coverage.load()
    if not coverage.get_data().measured_files():
        raise SystemExit("No hay datos de cobertura")
    filas = []
    for ruta in ARCHIVOS:
        _, lineas, _, faltantes, _ = coverage.analysis2(str(ROOT / "src/modules" / ruta))
        filas.append({"archivo": ruta, "lineas": len(lineas), "cubiertas": len(lineas) - len(faltantes),
                      "faltantes": faltantes})
    total = sum(f["lineas"] for f in filas)
    cubiertas = sum(f["cubiertas"] for f in filas)
    porcentaje = 100 * cubiertas / total if total else 0
    resultado = {"scope": "12 archivos de núcleo de reportes/auditoría y entidades de usuario/categoría",
                 "unit_tests": len(casos), "covered": cubiertas, "statements": total,
                 "percent": round(porcentaje, 2), "minimum": 80, "passed": porcentaje >= 80, "files": filas}
    (ROOT / "reports/rf044-050-unit-gate.json").write_text(json.dumps(resultado, indent=2), encoding="utf-8")
    print(f"Nucleo RF-044..050: {cubiertas}/{total} lineas = {porcentaje:.2f}% (minimo 80%)")
    return 0 if porcentaje >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
