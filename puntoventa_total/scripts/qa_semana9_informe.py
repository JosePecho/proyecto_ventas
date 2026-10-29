"""Genera el informe completo desde codigo y evidencia local, sin inventar tiempos."""
from __future__ import annotations

import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    document = (ROOT / "docs/testing/semana9_plantilla.md").read_text(encoding="utf-8")

    def code(match):
        path = match.group(1)
        extension = {".py": "python", ".toml": "toml", ".json": "json"}[Path(path).suffix]
        content = (ROOT / path).read_text(encoding="utf-8").rstrip()
        return f"**Ruta: `{path}`**\n\n```{extension}\n{content}\n```"

    document = re.sub(r"\{\{code:([^}]+)\}\}", code, document)
    rows = ["| Suite | Casos | Fallos / errores / skips | Pytest (s) | Pared (s) | Salida |",
            "| :--- | ---: | :--- | ---: | ---: | ---: |"]
    measurements = {}
    for name in ("completa", "core", "ventas", "inventario", "catalogo", "fast", "slow", "core-fast", "minor"):
        summary = json.loads((ROOT / f"reports/semana9/{name}.json").read_text(encoding="utf-8"))
        xml = ET.parse(ROOT / f"reports/semana9/{name}.xml").getroot()
        suite = xml if xml.tag == "testsuite" else xml.find("testsuite")
        elapsed = float(suite.attrib["time"])
        measurements[name] = summary["wall_seconds"]
        stats = "/".join(suite.attrib.get(key, "0") for key in ("failures", "errors", "skipped"))
        rows.append(f"| {name} | {suite.attrib['tests']} | {stats} | {elapsed:.3f} | "
                    f"{summary['wall_seconds']:.3f} | {summary['exit_code']} |")
    rows.append("\nSalida real de la suite completa (extracto):\n\n```text")
    log = (ROOT / "reports/semana9/completa.log").read_text(encoding="utf-8")
    rows.extend(line for line in log.splitlines()
                if "collected " in line or " passed" in line or "platform win32" in line)
    rows.append("```")
    original = (ROOT / "reports/semana9/auditoria-original.log").read_text(encoding="utf-8")
    mutant = (ROOT / "reports/semana9/auditoria-mutante.log").read_text(encoding="utf-8")
    rows.append("\nAuditoría real (extracto):\n\n```text")
    rows.extend(line for line in original.splitlines() if "1 passed" in line)
    rows.extend(line for line in mutant.splitlines() if "DID NOT RAISE" in line or "1 failed" in line)
    rows.append("```\n\nEl fallo del mutante es intencional y constituye la evidencia de detección.")
    document = document.replace("{{results}}", "\n".join(rows))
    complete, fast = measurements["completa"], measurements["core-fast"]
    saved = complete - fast
    reflection = (f"**R (Retorno):** «En esta medición local, completa tardó {complete:.3f} s de pared "
                  f"y Core/Fast {fast:.3f} s: diferencia {saved:.3f} s "
                  f"({saved / complete * 100:.1f}% respecto a completa). "
                  "Es una observación de un universo de 34 casos, no una predicción del ahorro total de CI. "
                  "El orden, las cachés y la carga del equipo influyen; para estimar CI mediré varias repeticiones "
                  "en el mismo runner y compararé medianas. Si ejecuto también la regresión completa, "
                  "la prioridad mejora el tiempo hasta detectar fallos, pero no ahorra ese trabajo total.»")
    document = document.replace("{{reflection}}", reflection)
    (ROOT / "docs/testing/semana9_informe.md").write_text(document, encoding="utf-8")
    print("Informe generado: docs/testing/semana9_informe.md")


if __name__ == "__main__":
    main()
