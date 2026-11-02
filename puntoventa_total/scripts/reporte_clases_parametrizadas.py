"""Inventario de ejecucion por clase a partir de pytest-cov --cov-context=test.

No considera la importacion de una clase como ejecucion de sus metodos.
La cobertura de lineas no garantiza cobertura de todos los comportamientos.
"""
import ast
import json
from pathlib import Path
from xml.etree import ElementTree

RAIZ = Path(__file__).resolve().parents[1]


def generar():
    informe = json.loads((RAIZ / "reports/parametrizadas_cobertura.json").read_text(encoding="utf-8"))
    archivos = {ruta.replace("\\", "/"): datos for ruta, datos in informe["files"].items()}
    if not any(datos.get("contexts") for datos in archivos.values()):
        raise SystemExit("El JSON no contiene contextos; ejecutar con tests/parametrizadas.coveragerc y --cov-context=test")
    filas = []
    for archivo in sorted((RAIZ / "src").rglob("*.py")):
        ruta = archivo.relative_to(RAIZ).as_posix()
        if "/migrations/" in ruta:
            continue
        arbol = ast.parse(archivo.read_text(encoding="utf-8-sig"))
        datos = archivos.get(ruta, {})
        ejecutadas = set(datos.get("executed_lines", []))
        contextos = datos.get("contexts", {})
        for clase in (n for n in arbol.body if isinstance(n, ast.ClassDef)):
            lineas = set()
            for metodo in clase.body:
                if not isinstance(metodo, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                for sentencia in metodo.body:
                    if isinstance(sentencia, ast.Expr) and isinstance(sentencia.value, ast.Constant):
                        if isinstance(sentencia.value.value, str) or sentencia.value.value is Ellipsis:
                            continue
                    if isinstance(sentencia, ast.Raise):
                        error = sentencia.exc.func if isinstance(sentencia.exc, ast.Call) else sentencia.exc
                        if isinstance(error, ast.Name) and error.id == "NotImplementedError":
                            continue
                    lineas.update(range(sentencia.lineno, sentencia.end_lineno + 1))
            # Solo lineas que coverage reconoce como ejecutables.
            medibles = lineas & (ejecutadas | set(datos.get("missing_lines", [])))
            parametrizadas = {
                linea for linea in medibles
                if any("[" in contexto and contexto.endswith("|run") for contexto in contextos.get(str(linea), []))
            }
            estado = "ejecutada" if parametrizadas else ("pendiente" if medibles else "sin cuerpo medible")
            filas.append((ruta, clase.name, len(parametrizadas), len(medibles), estado))
    salida = [
        "# Inventario de clases y pruebas parametrizadas", "",
        "Medicion de cuerpos de metodos; excluye migraciones. No cuenta importaciones ni declara cobertura funcional completa.",
        "Las clases sin cuerpo medible incluyen DTOs, enums e interfaces; sus contratos pueden probarse desde otras clases.", "",
        "| Archivo | Clase | Lineas en casos parametrizados | Lineas medibles | Estado |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    junit = RAIZ / "reports/parametrizadas_resultados.xml"
    if junit.exists():
        casos = ElementTree.parse(junit).findall(".//testcase")
        nuevos = [caso for caso in casos if "parametriz" in caso.get("classname", "")]
        fallos = [caso for caso in casos if caso.find("failure") is not None or caso.find("error") is not None]
        resumen = f"JUnit: {len(casos)} casos; {len(nuevos)} nuevos parametrizados; {len(fallos)} fallos/errores."
        salida[2:2] = [resumen, ""]
        print(resumen)
    salida.extend(f"| {ruta} | {nombre} | {cubiertas} | {total} | {estado} |" for ruta, nombre, cubiertas, total, estado in filas)
    destino = RAIZ / "reports/parametrizadas_clases.md"
    destino.write_text("\n".join(salida) + "\n", encoding="utf-8")
    for estado in ("ejecutada", "pendiente", "sin cuerpo medible"):
        print(f"{estado}: {sum(fila[4] == estado for fila in filas)}")
    print(f"Informe: {destino}")


if __name__ == "__main__":
    generar()
