"""Demuestra que el test RN-08 detecta un mutante sin editar produccion."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CASE = "tests/unit/domain/test_calculadora_venta.py::test_vuelto_negativo_lanza_pago_insuficiente"


class MutacionPago:
    def pytest_configure(self, config):
        from src.modules.sales.domain.services.calculadora_venta import CalculadoraVenta
        from src.shared.domain.value_objects.monto import Monto

        # BUG deliberado: convierte un pago insuficiente en vuelto cero.
        CalculadoraVenta.vuelto = classmethod(
            lambda cls, total, pagado: Monto(max(0, pagado.valor - total.valor), total.moneda)
        )


def main() -> int:
    if "--mutante" in sys.argv:
        sys.path.insert(0, str(ROOT))
        import pytest

        return pytest.main([CASE, "-v", "-o", "cache_dir=reports/semana9/.pytest_cache",
                            "--junitxml=reports/semana9/auditoria-mutante.xml"],
                           plugins=[MutacionPago()])
    reports = ROOT / "reports/semana9"
    reports.mkdir(parents=True, exist_ok=True)
    commands = {
        "original": [sys.executable, "-m", "pytest", CASE, "-v", "-o",
                     "cache_dir=reports/semana9/.pytest_cache"],
        "mutante": [sys.executable, str(Path(__file__).resolve()), "--mutante"],
    }
    codes = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", check=False)
        output = result.stdout + result.stderr
        (reports / f"auditoria-{name}.log").write_text(output, encoding="utf-8")
        print(output)
        codes[name] = result.returncode
    report = reports / "auditoria-mutante.xml"
    if codes != {"original": 0, "mutante": 1} or not report.exists():
        return 1
    cases = ET.parse(report).findall(".//testcase")
    failures = [case.find("failure") for case in cases if case.find("failure") is not None]
    detected = (len(cases) == 1 and len(failures) == 1
                and "DID NOT RAISE" in failures[0].get("message", ""))
    print("Mutante detectado por RN-08." if detected else "Auditoria inconclusa.")
    return 0 if detected else 1


if __name__ == "__main__":
    raise SystemExit(main())
