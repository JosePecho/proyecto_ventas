"""Ejecuta suites acotadas sin reimportar ni duplicar los tests existentes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    manifest = json.loads((ROOT / "tests/suites/semana9.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=manifest["suites"])
    args = parser.parse_args()
    reports = ROOT / "reports/semana9"
    reports.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "pytest", *manifest["paths"],
               "-vv", "--durations=0", "-o", "console_output_style=classic",
               "-o", "cache_dir=reports/semana9/.pytest_cache",
               f"--junitxml={reports / (args.suite + '.xml')}"]
    expression = manifest["suites"][args.suite]
    if expression:
        command.extend(["-m", expression])
    start = perf_counter()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", check=False)
    elapsed = perf_counter() - start
    output = result.stdout + result.stderr
    print(output)
    (reports / f"{args.suite}.log").write_text(output, encoding="utf-8")
    summary = {"suite": args.suite, "expression": expression, "command": command,
               "wall_seconds": round(elapsed, 6), "exit_code": result.returncode}
    (reports / f"{args.suite}.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Suite {args.suite}: {elapsed:.3f}s; salida={result.returncode}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
