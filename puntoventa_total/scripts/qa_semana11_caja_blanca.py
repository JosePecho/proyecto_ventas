"""Reproduce McCabe, rango de caminos y cobertura de ProcesarPago.ejecutar."""
import ast
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/modules/sales/application/use_cases/procesar_pago.py"
EDGES = [
    (1, 2), (2, 3), (3, 4), (4, 26), (3, 5), (5, 6), (6, 7), (7, 8), (6, 8),
    (8, 9), (9, 10), (9, 12), (10, 11), (10, 12), (11, 13), (12, 13),
    (13, 14), (14, 15), (15, 26), (14, 16), (16, 17), (17, 18), (17, 21),
    (18, 19), (18, 17), (19, 20), (19, 17), (20, 17), (21, 22), (22, 23),
    (22, 24), (23, 25), (24, 25), (25, 26),
]
START = [1, 2, 3, 5, 6, 8]
NO_CHANGE = [9, 12, 13, 14]
PARTIAL = [15, 26]
FULL = [16, 17, 21, 22, 24, 25, 26]
PATHS = {
    "B01": [1, 2, 3, 4, 26],
    "B02": START + NO_CHANGE + PARTIAL,
    "B03": [1, 2, 3, 5, 6, 7, 8] + NO_CHANGE + PARTIAL,
    "B04": START + [9, 10, 11, 13, 14] + PARTIAL,
    "B05": START + [9, 10, 12, 13, 14] + PARTIAL,
    "B06": START + NO_CHANGE + FULL,
    "B07": START + NO_CHANGE + [16, 17, 18, 19, 20, 17, 21, 22, 24, 25, 26],
    "B08": START + NO_CHANGE + [16, 17, 18, 17, 21, 22, 24, 25, 26],
    "B09": START + NO_CHANGE + [16, 17, 18, 19, 17, 21, 22, 24, 25, 26],
    "B10": START + [9, 10, 11, 13, 14, 16, 17, 21, 22, 23, 25, 26],
}


def rank(matrix):
    matrix = [[Fraction(value) for value in row] for row in matrix]
    pivot = 0
    for column in range(len(matrix[0])):
        candidate = next((row for row in range(pivot, len(matrix)) if matrix[row][column]), None)
        if candidate is None:
            continue
        matrix[pivot], matrix[candidate] = matrix[candidate], matrix[pivot]
        divisor = matrix[pivot][column]
        matrix[pivot] = [value / divisor for value in matrix[pivot]]
        for row in range(pivot + 1, len(matrix)):
            factor = matrix[row][column]
            matrix[row] = [value - factor * base for value, base in zip(matrix[row], matrix[pivot], strict=True)]
        pivot += 1
        if pivot == len(matrix):
            break
    return pivot


def main():
    source = SOURCE.read_bytes()
    tree = ast.parse(source.decode("utf-8"))
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "ejecutar")
    predicates = sum(
        len(node.values) - 1 if isinstance(node, ast.BoolOp) else 1
        for node in ast.walk(method) if isinstance(node, ast.If | ast.IfExp | ast.For | ast.While | ast.BoolOp)
    )
    matrix = []
    for path in PATHS.values():
        transitions = list(zip(path, path[1:], strict=False))
        assert all(edge in EDGES for edge in transitions)
        matrix.append([transitions.count(edge) for edge in EDGES])
    complexity = len(EDGES) - len({node for edge in EDGES for node in edge}) + 2
    assert complexity == predicates + 1 == rank(matrix) == 10
    coverage = json.loads((ROOT / "reports/semana11-cobertura.json").read_text(encoding="utf-8"))
    file = next(value for key, value in coverage["files"].items() if key.replace("\\", "/").endswith("use_cases/procesar_pago.py"))
    summary = file["summary"]
    assert summary["missing_lines"] == summary["missing_branches"] == 0
    test_results = {}
    for filename, expected in (("semana11-pruebas.xml", 38), ("semana11-rollback-mysql.xml", 9)):
        suites = ElementTree.parse(ROOT / "reports" / filename).getroot().findall(".//testsuite")
        counts = {key: sum(int(suite.get(key, "0")) for suite in suites)
                  for key in ("tests", "failures", "errors", "skipped")}
        assert counts["tests"] == expected and not any(counts[key] for key in ("failures", "errors", "skipped"))
        test_results[filename] = counts
    report = {
        "source": str(SOURCE.relative_to(ROOT)), "sha256": hashlib.sha256(source).hexdigest(),
        "method": "ProcesarPago.ejecutar", "predicates": predicates, "nodes": 26, "edges": len(EDGES),
        "connected_components": 1, "mccabe": complexity, "basis_rank": rank(matrix),
        "paths": PATHS, "edges_list": EDGES, "coverage_file": summary,
        "method_missing_lines": [line for line in file["missing_lines"] if method.lineno <= line <= method.end_lineno],
        "scope": "CFG explicito con cortocircuito; sin aristas de excepciones implicitas de colaboradores",
        "human_approval": "PENDIENTE",
        "test_results": test_results,
    }
    destination = ROOT / "reports/semana11-estructura.json"
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("predicates", "nodes", "edges", "mccabe", "basis_rank", "human_approval")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
