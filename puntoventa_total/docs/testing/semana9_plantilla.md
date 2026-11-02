# 1. RADIOGRAFÍA DE TU CÓDIGO ACTUAL (¿QUÉ TIENES CONSTRUIDO Y DÓNDE?)

## 1.1 Lenguaje, Framework (Frontend/Backend) y Motor de Pruebas asignado

PuntoVenta Total es un monolito modular Python con Django, Django REST Framework y arquitectura por dominio, aplicación e infraestructura. Tiene módulos de ventas, catálogo, inventario, caja, pedidos, identidad, clientes, promociones, reportes y auditoría. La interfaz usa plantillas Django y recursos estáticos; no se detectó un proyecto React/Angular para este laboratorio. El motor asignado es Pytest con pytest-django. Las unitarias ejercitan objetos Python reales; la integración seleccionada usa una base SQLite temporal creada por pytest-django.

Este laboratorio analiza exhaustivamente **los archivos enumerados abajo**, no certifica todos los módulos del repositorio. Todas las rutas siguientes son relativas a `puntoventa_total/`, salvo las que comienzan por `.github/`.

Versiones declaradas en `requirements/base.txt` y `requirements/testing.txt`: Django 5.2.18, pytest 8.2.0 y pytest-django 4.8.0; Python mínimo declarado 3.11. Versiones **observadas en esta ejecución**: Python 3.14.7, Django 6.1.2, pytest 9.1.1 y pytest-django 4.14.0, coincidentes con el perfil existente `requirements/qa-inventory.txt`. No se afirma haber validado aquí el perfil de producción.

## 1.2 Inventario del Código Analizado

| Archivo / Componente / Clase | Ruta Actual Detectada | Qué hace actualmente | Riesgo | ¿Tiene Tests? |
| :--- | :--- | :--- | :--- | :--- |
| CalculadoraVenta | `src/modules/sales/domain/services/calculadora_venta.py` | Subtotal, descuentos, total, desglose IGV y vuelto; `calcular_linea` lanza NotImplementedError | Core | `tests/unit/domain/test_calculadora_venta.py` |
| DetalleVenta | `src/modules/sales/domain/entities/detalle_venta.py` | Valida cantidad positiva, calcula subtotal/total, aplica descuento 0–100%, recalcula al cambiar cantidad | Core | Mismo archivo de calculadora |
| Monto | `src/shared/domain/value_objects/monto.py` | Decimal, ROUND_HALF_UP, montos no negativos, moneda consistente y porcentajes | Core | Mismo archivo de calculadora |
| Existencia | `src/modules/inventory/domain/entities/existencia.py` | Entradas/salidas, disponibilidad, reservas, confirmación y umbral mínimo | Core | `tests/unit/domain/test_stock.py` |
| Lote | `src/modules/inventory/domain/entities/lote.py` | Existencias por lote y vencimiento; usado en planificación de salida | Core | Mismo archivo de stock |
| PoliticaStock | `src/modules/inventory/domain/services/politica_stock.py` | Planifica salida priorizando vencimiento próximo según comportamiento del test existente | Core | Mismo archivo de stock |
| ReservaStock | `src/modules/inventory/domain/entities/reserva_stock.py` | Vigencia, expiración, confirmación, liberación y extensión | Core | Mismo archivo de stock |
| Producto | `src/modules/catalog/domain/entities/producto.py` | Nombre, precio, disponibilidad y descontinuación | Core / Minor para nombre vacío | `tests/unit/domain/test_producto.py` |
| Precio | `src/modules/catalog/domain/value_objects/precio.py` | Margen mínimo por defecto 10%, ganancia y descuento sin bajar del costo | Core | Mismo archivo de producto |
| Fábrica de repositorio | `src/modules/catalog/infrastructure/factories.py` | Construye DjangoProductoRepository y otros adaptadores | Core | `tests/integration/test_producto_repository.py` |
| DjangoProductoRepository | `src/modules/catalog/infrastructure/persistence/repositories/django_producto_repository.py` | Guarda, busca por código y lista productos; rechaza código duplicado | Core | Mismo archivo de integración |
| Configuración de pruebas | `pyproject.toml`, `config/settings/testing.py`, `tests/conftest.py`, `tests/unit/conftest.py` | Descubrimiento, fixtures, aislamiento de BD y comprobación opcional de skips | Soporte | Utilizada en las ejecuciones |

La asignación `Minor` a nombre vacío expresa prioridad relativa frente a pérdida monetaria, sobreventa o duplicados; sigue siendo una validación obligatoria y se ejecuta en la regresión completa del laboratorio.

Hallazgos concretos de la revisión, además de la organización de suites:

- `CalculadoraVenta.calcular_linea` permanece sin implementar y su mensaje recomienda `DetalleVenta.directo()`, método que no existe en la clase analizada. El código actual crea líneas con el constructor. Se debe corregir ese contrato antes de consumir este método.
- La política llamada PEPS ordena primero por vencimiento y después por recepción; ese comportamiento corresponde a prioridad por vencimiento (FEFO). El test comprueba lo que hace actualmente. Confirmar con el docente/negocio si se exige PEPS estricto por recepción antes de cambiar algoritmo o expectativa.
- `CalculadoraVenta.vuelto` resta valores sin verificar que total y pagado tengan la misma moneda, mientras `Monto.__sub__` sí aplica esa validación. Este caso no está cubierto por las pruebas seleccionadas y debe acordarse y probarse si se aceptan pagos multimoneda.
- Los tests analizados cubren escenarios concretos, no todos los métodos ni todas las ramas del inventario. No se calculó ni se afirma cobertura completa del producto.

## 1.3 Diagnóstico del Cuello de Botella en tu Proyecto

El repositorio **ya tenía** etiquetas unit/integration/functional/e2e/system/uat/performance y CI por niveles. No partía de cero. Faltaban las dimensiones explícitas core/minor, fast/slow y componente para estos casos de dominio. Con más de 200 pruebas, seleccionar todo obliga a esperar preparación de BD, navegador y servicios para recibir feedback sobre un cálculo puro.

El workflow raíz `.github/workflows/full-quality.yml` ya ejecuta niveles individuales y después una regresión global con cobertura: esa segunda pasada tiene un propósito de cobertura, pero también costo. Se agregó un control temprano Core/Fast y la auditoría RN-08 antes de las unitarias existentes. Se conserva la regresión posterior. La carpeta `puntoventa_total/.github/workflows/` es interna al proyecto y GitHub Actions solo descubre automáticamente los workflows en `.github/workflows/` desde la raíz del repositorio.

Las etiquetas nuevas cubren únicamente cuatro archivos seleccionados. `pytest -m core` sobre todo el repositorio **no equivale todavía** a todas las reglas críticas del sistema. La ampliación requiere revisión de cada prueba restante. Las suites superpuestas se ejecutan por separado para demostrar los filtros; no se importan tests desde archivos barriles, evitando duplicar colección.

# 2. ¿QUÉ TIENES QUE HACER? (PLAN DE ACCIÓN DIRECTO)

Los pasos siguientes ya están implementados en este checkout:

1. Registrar siete marcadores nuevos en `pyproject.toml`, manteniendo `--strict-markers`.
2. Etiquetar los tres archivos unitarios de ventas, stock y producto y el archivo de integración del repositorio.
3. Crear `tests/suites/semana9.json`: universo acotado y nueve expresiones de selección.
4. Crear `scripts/qa_semana9.py`: ejecutor que conserva código de salida, registra duración de pared, consola y JUnit.
5. Crear `scripts/qa_semana9_auditoria.py`: ejecuta el caso original y un mutante en procesos independientes, y verifica que falle por la excepción de negocio ausente.
6. Añadir dos pasos al workflow raíz `.github/workflows/full-quality.yml`: Core/Fast y auditoría antes de las unitarias.
7. Ejecutar los comandos de la sección 6 y conservar `reports/semana9/` como evidencia. El documento completo se genera con `scripts/qa_semana9_informe.py` para mantener código y mediciones sincronizados.

# 3. ESTRUCTURA DE CARPETAS PROPUESTA (DÓNDE VA CADA ARCHIVO)

```text
proyecto_ventas/
|-- .github/workflows/full-quality.yml       # CI modificado
`-- puntoventa_total/
    |-- pyproject.toml                      # marcadores registrados
    |-- requirements/qa-inventory.txt       # perfil QA existente
    |-- config/settings/testing.py          # SQLite temporal existente
    |-- src/
    |   |-- shared/domain/value_objects/monto.py
    |   `-- modules/
    |       |-- sales/domain/{entities,services}/
    |       |-- inventory/domain/{entities,services}/
    |       `-- catalog/{domain,infrastructure}/
    |-- tests/
    |   |-- conftest.py
    |   |-- unit/domain/
    |   |   |-- test_calculadora_venta.py
    |   |   |-- test_stock.py
    |   |   `-- test_producto.py
    |   |-- integration/test_producto_repository.py
    |   `-- suites/semana9.json
    |-- scripts/
    |   |-- qa_semana9.py
    |   |-- qa_semana9_auditoria.py
    |   `-- qa_semana9_informe.py
    |-- docs/testing/
    |   |-- semana9_plantilla.md
    |   `-- semana9_informe.md
    `-- reports/semana9/
        |-- {suite}.log
        |-- {suite}.xml
        |-- {suite}.json
        |-- auditoria-original.log
        |-- auditoria-mutante.log
        `-- auditoria-mutante.xml
```

# 4. LABORATORIO ABP — PASO 1: MAPEO LÓGICO DE TUS 3+ SUITES

| ID Caso | Componente / Función Real a Probar | Suite por Componente | Suite por Riesgo | Suite por Tiempo | Etiqueta / Tag Aplicado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S9-01 | `CalculadoraVenta.vuelto`: 10 pagado con 5 lanza PagoInsuficiente y faltante 5 | ventas | Core | Fast | `core, fast, ventas` |
| S9-02 | `CalculadoraVenta.total`: 2×8.50 + 4 con 10% de descuento resulta 20.60 | ventas | Core | Fast | `core, fast, ventas` |
| S9-03 | `CalculadoraVenta.desglose_igv`: 118 = 100 base + 18 IGV | ventas | Core | Fast | `core, fast, ventas` |
| S9-04 | `Monto`: 2.345 redondea a 2.35 | ventas (dependencia monetaria) | Core | Fast | `core, fast, ventas` |
| S9-05 | `DetalleVenta.aplicar_descuento_pct`: rechaza -1 y 101 | ventas | Core | Fast | `core, fast, ventas` |
| S9-06 | `Existencia.reservar`: reservar 4 de 5 deja 1; reservar 2 más falla | inventario | Core | Fast | `core, fast, inventario` |
| S9-07 | `Producto`: rechaza nombre vacío | catalogo | Minor | Fast | `minor, fast, catalogo` |
| S9-08 | `Precio`: rechaza venta 5 con costo 10 | catalogo | Core | Fast | `core, fast, catalogo` |
| S9-09 | Repositorio: rechaza código de barras duplicado sobre BD | catalogo | Core | Slow | `core, slow, catalogo, integration, django_db` |

Hay **34 casos ejecutables**, contando parametrizaciones, en cuatro archivos. La tabla selecciona nueve escenarios representativos. Fast describe dominio sin infraestructura, no un umbral arbitrario de milisegundos; Slow representa BD real temporal. La preparación de Django también consume tiempo en Fast, aunque no crea la BD. `ventas` incluye sus dependencias monetarias, por ubicación del archivo probado.

# 5. LABORATORIO ABP — PASO 2: CÓDIGO COMPLETO DE TUS PRUEBAS Y SUITES

## 5.1 Archivo de Configuración del Motor de Pruebas

Pytest traduce `@Tag` de JUnit a `@pytest.mark`, `@IncludeTags` a `-m` y `@SelectClasses` al listado de archivos del manifiesto. No necesita crear clases Java artificiales. Se usa la configuración existente en pyproject.toml; no se añade un pytest.ini que la reemplace accidentalmente.

{{code:pyproject.toml}}

## 5.2 Código de las Pruebas Unitarias Etiquetadas

Se reutilizan las pruebas reales existentes y se añaden etiquetas; no se sustituyen sus aserciones por expectativas más permisivas. El listado siguiente es el contenido completo de los cuatro archivos ejecutados, incluyendo integración para contrastar Fast/Slow.

{{code:tests/unit/domain/test_calculadora_venta.py}}

{{code:tests/unit/domain/test_stock.py}}

{{code:tests/unit/domain/test_producto.py}}

{{code:tests/integration/test_producto_repository.py}}

## 5.3 Código de las 3+ Suites Organizadoras

1. Riesgo crítico: `core`; adicionalmente `minor` permite revisar validaciones menores.
2. Componente: `ventas`, `inventario` y `catalogo`.
3. Tiempo: `fast` y `slow`; `core-fast` combina prioridad y costo.
4. `completa` ejecuta el universo de 34 casos del laboratorio; **no significa toda la suite del repositorio**.

Los organizadores son expresiones sobre los mismos nodos Pytest. Cada invocación recoge cada prueba una sola vez; un caso puede pertenecer legítimamente a varias dimensiones.

{{code:tests/suites/semana9.json}}

{{code:scripts/qa_semana9.py}}

# 6. LABORATORIO ABP — PASO 3: ¿CÓMO EJECUTAR LAS PRUEBAS LUEGO? (GUÍA PASO A PASO EN TERMINAL)

## 6.1 Paso 1: Instalación de dependencias

En PowerShell, desde la carpeta del repositorio:

```powershell
Set-Location 'C:\Users\mallq\OneDrive\Desktop\proyecto_ventas\puntoventa_total'
# Si ya existe .venv, comprobarlo sin reinstalar:
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pytest --version
```

Para una instalación desde cero del **perfil QA que se ejecutó**, instala primero Python 3.14.7 y usa un entorno nuevo, sin reemplazar tu entorno existente:

```powershell
py -3.14 -m venv .venv-semana9
.\.venv-semana9\Scripts\python.exe -m pip install --upgrade pip
.\.venv-semana9\Scripts\python.exe -m pip install -r requirements/qa-tools.txt
.\.venv-semana9\Scripts\python.exe -m pip check
```

El perfil `qa-tools.txt` incorpora el perfil QA/MySQL existente y las herramientas Ruff, Freezegun, Responses y pytest-xdist instaladas posteriormente a petición del usuario. Incluye dependencias de otros niveles de QA, aunque este laboratorio solo usa Pytest/Django y SQLite. No hace falta descargar Chromium ni iniciar MySQL/Redis para estos cuatro archivos. Se completaron las dependencias del `.venv` existente; no se creó un entorno desde cero. Si usas `.venv-semana9`, reemplaza `.venv` por `.venv-semana9` en todos los comandos siguientes. No necesitas activar el entorno ni cambiar la política de ejecución de PowerShell. Los comandos del estudiante no dependen de RTK, herramienta usada por el asistente en esta sesión.

## 6.2 Paso 2: Comandos de Ejecución Selectiva (Uno por cada Suite)

```powershell
# SOLO Core (33 casos, incluyendo 3 de BD):
.\.venv\Scripts\python.exe scripts/qa_semana9.py core
# SOLO componente ventas (20 casos):
.\.venv\Scripts\python.exe scripts/qa_semana9.py ventas
# SOLO Fast, excluyendo Slow (31 casos):
.\.venv\Scripts\python.exe scripts/qa_semana9.py fast
# Otros filtros y contraste:
.\.venv\Scripts\python.exe scripts/qa_semana9.py inventario
.\.venv\Scripts\python.exe scripts/qa_semana9.py catalogo
.\.venv\Scripts\python.exe scripts/qa_semana9.py slow
.\.venv\Scripts\python.exe scripts/qa_semana9.py core-fast
.\.venv\Scripts\python.exe scripts/qa_semana9.py minor
.\.venv\Scripts\python.exe scripts/qa_semana9.py completa
# Auditoría: el proceso padre retorna cero solo si el mutante falla por RN-08:
.\.venv\Scripts\python.exe scripts/qa_semana9_auditoria.py
# Regenerar este informe con archivos y mediciones actuales:
.\.venv\Scripts\python.exe scripts/qa_semana9_informe.py
```

También puedes comprobar la equivalencia con xUnit directamente:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/domain/test_calculadora_venta.py -m 'core and fast and not slow' -v --durations=0 -o cache_dir=reports/semana9/.pytest_cache
.\.venv\Scripts\python.exe -m pytest tests/unit/domain/test_calculadora_venta.py -m ventas -v --durations=0 -o cache_dir=reports/semana9/.pytest_cache
```

Para toda la regresión del repositorio usa sus workflows existentes y requisitos de servicios. Este informe solo valida el universo seleccionado. El runner devuelve errores y también el código 5 de Pytest si no se seleccionan tests; no convierte un filtro vacío en éxito. `QA_REQUIRE_ALL_TESTS=1`, ya disponible en CI, hace fallar sesiones con skips/xfails; la deselección por `-m` es deliberada y diferente de omitir casos con skip.

## 6.3 Paso 3: Ejemplo de Logs de Consola y Medición de Tiempos (Entregable)

{{results}}

Los `.log` contienen salida real con cada caso y sus duraciones; los `.xml` permiten mostrar resultados en CI; los `.json` guardan comando exacto, filtro, tiempo de pared medido con perf_counter y código de salida. Toma capturas donde se vea el comando, el conteo passed/deselected y la duración. Conserva también el fallo intencional de `auditoria-mutante.log` junto con el éxito del original.

Tiempo de Pytest y tiempo de pared **no son lo mismo**: este último incluye arranque del intérprete, plugins, carga de Django y finalización del proceso. Las duraciones de cada caso pueden redondear a cero; `-vv --durations=0` conserva todas. La caché del runner se guarda en `reports/semana9/.pytest_cache`, ya que la caché antigua de la carpeta del proyecto presentó restricciones de acceso. No se modificó ni eliminó esa caché antigua.

# 7. PUNTO DE CONTROL OBLIGATORIO: AUDITORÍA IA (SELF-HEALING TESTING)

## 7.1 El Fallo Real y la Trampa del Self-Healing Autónomo

Regla documentada en el test existente: **RN-08**, un pago de S/5 para un total de S/10 debe lanzar `PagoInsuficiente` y exponer faltante 5. Un mutante equivocado reemplaza la excepción por vuelto cero:

```python
# BUG deliberado: acepta silenciosamente un pago insuficiente.
return Monto(max(0, pagado.valor - total.valor), total.moneda)
```

Ante ese bug, una supuesta reparación automática podría proponer lo siguiente:

```python
# SUGERENCIA IA RECHAZADA; no forma parte de las pruebas instaladas.
assert CalculadoraVenta.vuelto(Monto('10.00'), Monto('5.00')).valor == Decimal('0.00')
```

Esta aserción daría verde al mutante, pero solo describe su resultado incorrecto. También sería inválido reclasificar el caso como Minor/Slow para retirarlo del gate Core/Fast, añadir xfail/skip o capturar indiscriminadamente excepciones. Un cambio de etiquetas no resuelve una pérdida de S/5.

Se ejecutó la mutación en memoria dentro de un **subproceso independiente**. El archivo de producción permanece con su regla correcta y el proceso original se ejecuta antes del mutante. La herramienta comprueba exactamente un caso fallido con `DID NOT RAISE`, además de los códigos 0 del original y 1 del mutante: un error de importación o configuración no cuenta como detección del bug.

{{code:scripts/qa_semana9_auditoria.py}}

## 7.2 Validación Manual (Beck, 2022) y Defensa Técnica

Validación que el estudiante debe revisar y defender: total 10, pago 5, diferencia -5, faltante 5. La precondición de cobro válido no se cumple. La excepción impide tratar ese pago como una operación válida. Se conserva la aserción contractual:

```python
with pytest.raises(PagoInsuficiente) as exc:
    CalculadoraVenta.vuelto(Monto(Decimal('10.00')), Monto(Decimal('5.00')))
assert exc.value.faltante == 5.0
```

La corrección de implementación que debe conservarse es:

```python
diferencia = pagado.valor - total.valor
if diferencia < 0:
    raise PagoInsuficiente(float(-diferencia))
return Monto(diferencia, total.moneda)
```

**Defensa técnica para el informe:** «Rechacé la propuesta de cambiar la expectativa a cero porque modificaba el oráculo a partir del comportamiento defectuoso. RN-08 exige rechazar el pago insuficiente y reportar S/5 faltantes; obtener verde no autoriza aceptar una venta incompleta. Conservé la expectativa de excepción, comprobé que el original pasa y que el mutante falla específicamente por ausencia de esa excepción. La validación del requerimiento precede a cualquier ajuste de tests o etiquetas. La demostración automatizada aporta evidencia; mi revisión de la regla y mi aceptación final constituyen el control humano.»

La denominación «Beck, 2022» proviene de la consigna. No se recibió título, página ni edición y no se inventa una cita textual o referencia bibliográfica. Completa esa referencia con el material exacto del docente. Tampoco se presenta esta ejecución automatizada como si una persona hubiera firmado ya la validación manual: el estudiante debe revisar y ratificar el cálculo anterior.

# 8. RESUMEN DE ENTREGABLES (C7.I2) Y REFLEXIÓN A.I.R.E.

## 8.1 Verificación de los 3 Entregables de Sesión

| Entregable | Artefactos | Estado |
| :--- | :--- | :--- |
| Código Suites | Marcadores en pyproject.toml, cuatro archivos etiquetados, `tests/suites/semana9.json`, `scripts/qa_semana9.py` | Implementado y ejecutado en el perfil QA local |
| Logs de Ejecución Selectiva | `reports/semana9/{suite}.log`, `.xml`, `.json` para nueve suites | Resultados reales, detallados en 6.3 |
| Auditoría IA | `scripts/qa_semana9_auditoria.py`, logs original/mutante y JUnit del mutante | Original verde; mutante debe fallar por RN-08. Requiere ratificación manual del estudiante |

El workflow raíz se modificó para priorizar Core/Fast y conservar evidencia con su upload-artifact existente. No se afirma haber ejecutado GitHub Actions remotamente ni toda la regresión del sistema en esta intervención.

Comprobaciones adicionales: sintaxis de los tres scripts y consistencia de espacios del diff. En la intervención posterior se instaló Ruff 0.4.4: `python -m ruff check src config scripts tests --select F821,F822,F823,E9` pasó. `python -m pip check` también pasó tras completar las dependencias.

## 8.2 Reflexión A.I.R.E. personalizada al proyecto

**A (Aprendizaje):** «Aprendí a traducir las suites y tags de xUnit a Pytest utilizando marcadores registrados, rutas de archivos y expresiones `-m`. Separé reglas monetarias y de stock de las pruebas que necesitan persistencia sin duplicar los casos.»

**I (Interacción):** «Audité una sugerencia de Self-Healing que aceptaría pago insuficiente a cambio de obtener un test verde. Contrasté el resultado con RN-08 y mantuve el oráculo de excepción y faltante. La mutación reproducible muestra por qué la sugerencia debe rechazarse; revisaré y ratificaré manualmente esa regla antes de entregar.»

{{reflection}}

**E (Entorno):** «Las etiquetas permiten feedback temprano y regresión posterior, mientras los logs y JUnit hacen revisable la evidencia. El manifiesto acota el alcance: debo extender la clasificación al resto del sistema antes de llamar Core a todas sus reglas críticas. Conservar las aserciones de negocio mejora la confiabilidad de los cambios asistidos por IA.»
