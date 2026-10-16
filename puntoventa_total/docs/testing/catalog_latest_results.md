# Resultado de testing del Catalogo Web — RF-025 a RF-029

Ejecucion terminada: 2026-10-16T21:11:49.494399+00:00.
Entorno: Python 3.14.7, Django 6.1.2, MySQL 8.4.3/InnoDB real
en instancia nativa desechable y Chromium obligatorio.

| Nivel del catalogo | Casos | Resultado |
|---|---|---|
| Unitarias | 13 | Aprobadas |
| Integracion | 26 | Aprobadas |
| Sistema y carga | 3 | Aprobadas |
| Aceptacion BDD | 4 | Aprobadas |
| Total del catalogo | 46 | Aprobadas |
| Regresion completa de todos los modulos | 346 | Aprobadas |

**0 fallos, 0 errores, 0 omisiones y 0 xfail. Codigo de salida: 0.**

La cobertura unitaria de los cuatro archivos seleccionados de aplicacion y DTO
es 100.00 % de lineas, frente al gate de 80 %. No representa cobertura
de todo el modulo catalog ni cobertura de ramas.

Carga publica: 20 peticiones, 4 trabajadores,
respuestas HTTP y contenido validados sin errores, p95 257.06 ms frente
al limite de 2000 ms. Es una carga pequena; no prueba capacidad productiva.

Se verificaron acceso anonimo, precio y stock vigentes, cinco categorias,
busqueda combinada con filtros, pagina 2, detalle con imagen cargada por HTTP,
Agotado tras vender la ultima unidad, productos ocultos y entradas maliciosas.
La regresion completa tambien incluye las cinco pruebas de concurrencia del
inventario. Django system check termino sin problemas.

Persisten advertencias existentes de fechas naive, deprecaciones y claves de
cache. No se ocultaron como errores esperados ni se cambiaron tests para esta
repeticion. Una ejecucion aprobada no garantiza ausencia absoluta de flakiness.

## Artefactos

- reports/catalog-regression.xml y catalog-regression.json
- reports/catalog-unit-coverage.xml y catalog-unit-coverage.json
- reports/catalog-load.json
- reports/browser/*.zip

## Reproduccion desde puntoventa_total

```powershell
$qaMysql = Join-Path $env:TEMP 'qa-mysql-binaries/mysql-8.4.3-winx64'
.venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir $qaMysql --full
```

La ejecucion fue local, no una ejecucion de GitHub Actions ni de Docker.
Los cuatro escenarios BDD aprobaron; la aceptacion humana permanece separada.
El plan, codigo completo y pipeline estan en [catalog_master_plan.md](catalog_master_plan.md).
