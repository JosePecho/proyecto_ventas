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

**Ruta: `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "puntoventa-total"
version = "1.0.0"
description = "Sistema integral de punto de venta, inventario y pedidos (Django Modular Monolith - Clean Architecture)"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }

[tool.setuptools]
packages = { find = { include = ["config*", "src*"] } }

[tool.ruff]
line-length = 110
target-version = "py311"
exclude = ["**/migrations/*", ".venv", "staticfiles"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
DJANGO_SETTINGS_MODULE = "config.settings.testing"
python_files = ["test_*.py"]
addopts = "-ra --strict-markers --tb=short"
markers = [
    "core: reglas criticas de negocio auditadas en Semana 9",
    "minor: validaciones de menor riesgo relativo",
    "fast: dominio puro sin infraestructura",
    "slow: requiere infraestructura o base de datos",
    "ventas: componente de calculo y detalle de venta",
    "inventario: componente de existencias y reservas",
    "catalogo: componente de productos y persistencia",
    "unit: pruebas de dominio/aplicacion sin infraestructura",
    "integration: pruebas con base de datos",
    "functional: pruebas de vistas/flujo HTTP",
    "e2e: pruebas de extremo a extremo",
    "system: pruebas de sistema (flujo HTTP completo con BD real)",
    "uat: pruebas de aceptacion BDD (Gherkin)",
    "performance: pruebas de rendimiento",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "src/modules/*/apps.py",
    "src/modules/*/models.py",
]

[tool.coverage.report]
fail_under = 80
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

## 5.2 Código de las Pruebas Unitarias Etiquetadas

Se reutilizan las pruebas reales existentes y se añaden etiquetas; no se sustituyen sus aserciones por expectativas más permisivas. El listado siguiente es el contenido completo de los cuatro archivos ejecutados, incluyendo integración para contrastar Fast/Slow.

**Ruta: `tests/unit/domain/test_calculadora_venta.py`**

```python
"""Nivel 1 - dominio: CalculadoraVenta y value objects.

Reglas aseguradas: RN-08 (el vuelto nunca es negativo), RN-17 (redondeo
ROUND_HALF_UP a 2 decimales), desglose IGV 18% y limites de descuento de linea.
"""
from decimal import Decimal

import pytest

from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.sales.domain.exceptions.venta_exceptions import PagoInsuficiente
from src.modules.sales.domain.services.calculadora_venta import CalculadoraVenta
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.unit, pytest.mark.core, pytest.mark.fast, pytest.mark.ventas]


def _linea(cantidad: int, precio: str, pct: str = "0") -> DetalleVenta:
    linea = DetalleVenta(
        venta_id="v1",
        producto_id="p1",
        producto_nombre="Pan",
        cantidad=cantidad,
        precio_unitario=Monto(Decimal(precio)),
    )
    if Decimal(pct):
        linea.aplicar_descuento_pct(Decimal(pct))
    return linea


# --- RN-08: vuelto ---------------------------------------------------------


def test_vuelto_exacto_es_cero():
    assert CalculadoraVenta.vuelto(Monto(Decimal("10.00")), Monto(Decimal("10.00"))).valor == Decimal("0.00")


def test_vuelto_mayor_al_total_devuelve_diferencia():
    vuelto = CalculadoraVenta.vuelto(Monto(Decimal("17.50")), Monto(Decimal("20.00")))
    assert vuelto.valor == Decimal("2.50")


def test_vuelto_negativo_lanza_pago_insuficiente():
    # RN-08: entrego S/ 5.00 por una venta de S/ 10.00
    with pytest.raises(PagoInsuficiente) as exc:
        CalculadoraVenta.vuelto(Monto(Decimal("10.00")), Monto(Decimal("5.00")))
    assert exc.value.faltante == 5.0


# --- totales del carrito ---------------------------------------------------


def test_subtotal_descuentos_y_total_de_varias_lineas():
    lineas = [_linea(2, "8.50"), _linea(1, "4.00", pct="10")]
    assert CalculadoraVenta.subtotal(lineas).valor == Decimal("21.00")
    assert CalculadoraVenta.descuentos(lineas).valor == Decimal("0.40")
    assert CalculadoraVenta.total(lineas).valor == Decimal("20.60")


def test_carrito_vacio_suma_cero():
    assert CalculadoraVenta.subtotal([]).valor == Decimal("0.00")
    assert CalculadoraVenta.descuentos([]).valor == Decimal("0.00")
    assert CalculadoraVenta.total([]).valor == Decimal("0.00")


def test_total_con_descuento_adicional_de_venta():
    descuento_venta = Monto(Decimal("2.10"))
    assert CalculadoraVenta.total([_linea(1, "8.50")], descuento_venta).valor == Decimal("6.40")


# --- IGV 18% ---------------------------------------------------------------


def test_desglose_igv_de_118_sep_diez_y_ocho():
    desglose = CalculadoraVenta.desglose_igv(Monto(Decimal("118.00")))
    assert desglose["base_imponible"] == 100.0
    assert desglose["igv"] == 18.0
    assert desglose["total"] == 118.0


def test_desglose_igv_redondea_base_a_dos_decimales():
    desglose = CalculadoraVenta.desglose_igv(Monto(Decimal("9.00")))
    assert desglose["base_imponible"] == 7.63  # 9 / 1.18 = 7.6271... -> 7.63
    assert desglose["igv"] == 1.37


# --- RN-17: redondeo y validacion de Monto ---------------------------------


def test_monto_redondea_hacia_arriba_en_empate():
    assert Monto(Decimal("2.345")).valor == Decimal("2.35")  # ROUND_HALF_UP


def test_monto_redondea_hacia_abajo_bajo_el_umbral():
    assert Monto(Decimal("2.344")).valor == Decimal("2.34")


def test_monto_acepta_float_y_lo_convierte():
    assert Monto(8.5).valor == Decimal("8.50")


def test_monto_negativo_es_rechazado():
    with pytest.raises(ValidationException):
        Monto(Decimal("-0.01"))


def test_monto_rechaza_operacion_con_moneda_distinta():
    with pytest.raises(ValidationException):
        Monto(Decimal("1.00"), "PEN") + Monto(Decimal("1.00"), "USD")


def test_resta_que_dejaria_saldo_negativo_es_rechazada():
    with pytest.raises(ValidationException):
        Monto(Decimal("5.00")) - Monto(Decimal("6.00"))


# --- limites de descuento de linea -----------------------------------------


def test_descuento_de_linea_en_rango_valido_se_aplica():
    linea = _linea(2, "8.50")
    linea.aplicar_descuento_pct(Decimal("25"))
    assert linea.descuento.valor == Decimal("4.25")
    assert linea.total.valor == Decimal("12.75")


@pytest.mark.parametrize("pct", ["-1", "101"])
def test_descuento_de_linea_fuera_de_rango_es_rechazado(pct):
    with pytest.raises(ValidationException):
        _linea(1, "8.50").aplicar_descuento_pct(Decimal(pct))


@pytest.mark.parametrize("cantidad", ["0", "-3"])
def test_cantidad_invalida_en_linea_es_rechazada(cantidad):
    with pytest.raises(ValidationException):
        DetalleVenta(
            venta_id="v1",
            producto_id="p1",
            producto_nombre="Pan",
            cantidad=int(cantidad),
            precio_unitario=Monto(Decimal("8.50")),
        )


def test_cambiar_cantidad_recalcula_descuento_proporcional():
    linea = _linea(1, "10.00", pct="20")
    linea.cambiar_cantidad(3)
    assert linea.subtotal.valor == Decimal("30.00")
    assert linea.descuento.valor == Decimal("6.00")
```

**Ruta: `tests/unit/domain/test_stock.py`**

```python
"""Invariantes de existencia, lotes, reservas y politica PEPS."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.unit, pytest.mark.core, pytest.mark.fast, pytest.mark.inventario]


def test_entrada_incrementa_stock_y_disponible():
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(10)
    assert existencia.cantidad == 10 and existencia.disponible == 10


def test_salida_supera_disponible_lanza_error():
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(3)
    with pytest.raises(StockInsuficiente):
        existencia.aplicar_salida(5)


def test_reserva_no_permite_doble_compromiso():
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(5)
    existencia.reservar(4)
    assert existencia.disponible == 1
    with pytest.raises(StockInsuficiente):
        existencia.reservar(2)


def test_confirmar_reserva_convierte_en_salida():
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(5)
    existencia.reservar(3)
    existencia.confirmar_reserva(3)
    assert existencia.cantidad == 2 and existencia.reservada == 0


def test_planificacion_peps_prefiere_vencimiento_mas_proximo():
    hoy = date.today()
    lote_viejo = Lote(producto_id="p1", numero_lote="L1", cantidad_inicial=5, cantidad_restante=5,
                      costo_unitario=Monto(Decimal("3")), fecha_vencimiento=hoy + timedelta(days=10))
    lote_nuevo = Lote(producto_id="p1", numero_lote="L2", cantidad_inicial=5, cantidad_restante=5,
                      costo_unitario=Monto(Decimal("3")), fecha_vencimiento=hoy + timedelta(days=100))
    plan = PoliticaStock.planificar_salida_peps([lote_nuevo, lote_viejo], 3)
    assert plan[0][0].numero_lote == "L1"


def test_reserva_expirada_no_esta_activa():
    reserva = ReservaStock(producto_id="p1", cantidad=1, referencia="PEDIDO:P1")
    reserva.expira_en = datetime.now() - timedelta(minutes=1)
    assert not reserva.activa

from datetime import datetime  # noqa: E402
```

**Ruta: `tests/unit/domain/test_producto.py`**

```python
"""Reglas de negocio del producto: precios, margen y descontinuacion."""
from decimal import Decimal

import pytest

from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.enums.estado_producto import EstadoProducto
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoDescontinuado
from src.modules.catalog.domain.value_objects.precio import Precio
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.unit, pytest.mark.fast, pytest.mark.catalogo]


@pytest.mark.core
def test_producto_se_crea_con_precio_valido(producto_faker):
    producto = producto_faker()
    assert producto.precio_venta.valor == Decimal("8.50")
    assert producto.disponible_para_vender


@pytest.mark.core
def test_producto_rechaza_precio_debajo_del_costo():
    with pytest.raises(ValidationException):
        Precio(costo=Monto(Decimal("10.00")), venta=Monto(Decimal("5.00")))


@pytest.mark.minor
def test_producto_rechaza_nombre_vacio():
    with pytest.raises(ValidationException):
        Producto(
            nombre="  ",
            codigo_barras="7751234567890",
            precio=Precio(costo=Monto(Decimal("1")), venta=Monto(Decimal("2"))),
        )


@pytest.mark.core
def test_descontinuar_bloquea_venta(producto_faker):
    producto = producto_faker()
    producto.descontinuar("fin de linea")
    assert producto.estado == EstadoProducto.DESCONTINUADO
    with pytest.raises(ProductoDescontinuado):
        producto.verificar_disponibilidad_venta()


@pytest.mark.core
def test_margen_minimo_se_respeta():
    with pytest.raises(ValidationException):
        Precio(costo=Monto(Decimal("100")), venta=Monto(Decimal("101")))
```

**Ruta: `tests/integration/test_producto_repository.py`**

```python
"""Repositorio de productos sobre base de datos real (pytest-django)."""
import pytest

from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.value_objects.precio import Precio
from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.integration, pytest.mark.django_db,
              pytest.mark.core, pytest.mark.slow, pytest.mark.catalogo]


def _crear(nombre="Cafe 250g", codigo="7759999000011"):
    return Producto(
        nombre=nombre,
        descripcion="Cafe de prueba",
        codigo_barras=codigo,
        precio=Precio(costo=Monto("4.00"), venta=Monto("9.00")),
    )


def test_guardar_y_buscar_por_codigo_barras():
    repo = construir_producto_repository()
    producto = _crear()
    repo.guardar(producto)

    encontrado = repo.buscar_por_codigo_barras("7759999000011")
    assert encontrado is not None
    assert encontrado.nombre == "Cafe 250g"


def test_codigo_barras_duplicado_se_rechaza():
    from src.modules.catalog.domain.exceptions.producto_exceptions import CodigoBarrasDuplicado

    repo = construir_producto_repository()
    repo.guardar(_crear())
    with pytest.raises(CodigoBarrasDuplicado):
        repo.guardar(_crear(nombre="Duplicado"))


def test_busqueda_por_termino():
    repo = construir_producto_repository()
    repo.guardar(_crear(nombre="Leche entera", codigo="7759999000022"))
    resultados = repo.listar(termino="leche")
    assert any(p.nombre == "Leche entera" for p in resultados)
```

## 5.3 Código de las 3+ Suites Organizadoras

1. Riesgo crítico: `core`; adicionalmente `minor` permite revisar validaciones menores.
2. Componente: `ventas`, `inventario` y `catalogo`.
3. Tiempo: `fast` y `slow`; `core-fast` combina prioridad y costo.
4. `completa` ejecuta el universo de 34 casos del laboratorio; **no significa toda la suite del repositorio**.

Los organizadores son expresiones sobre los mismos nodos Pytest. Cada invocación recoge cada prueba una sola vez; un caso puede pertenecer legítimamente a varias dimensiones.

**Ruta: `tests/suites/semana9.json`**

```json
{
  "paths": [
    "tests/unit/domain/test_calculadora_venta.py",
    "tests/unit/domain/test_stock.py",
    "tests/unit/domain/test_producto.py",
    "tests/integration/test_producto_repository.py"
  ],
  "suites": {
    "completa": "",
    "core": "core",
    "ventas": "ventas",
    "inventario": "inventario",
    "catalogo": "catalogo",
    "fast": "fast and not slow",
    "slow": "slow and not fast",
    "core-fast": "core and fast and not slow",
    "minor": "minor"
  }
}
```

**Ruta: `scripts/qa_semana9.py`**

```python
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
```

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

| Suite | Casos | Fallos / errores / skips | Pytest (s) | Pared (s) | Salida |
| :--- | ---: | :--- | ---: | ---: | ---: |
| completa | 34 | 0/0/0 | 5.531 | 16.469 | 0 |
| core | 33 | 0/0/0 | 8.301 | 19.369 | 0 |
| ventas | 20 | 0/0/0 | 2.580 | 15.106 | 0 |
| inventario | 6 | 0/0/0 | 4.032 | 17.483 | 0 |
| catalogo | 8 | 0/0/0 | 6.155 | 17.860 | 0 |
| fast | 31 | 0/0/0 | 1.434 | 14.941 | 0 |
| slow | 3 | 0/0/0 | 3.478 | 12.018 | 0 |
| core-fast | 30 | 0/0/0 | 1.811 | 14.116 | 0 |
| minor | 1 | 0/0/0 | 2.065 | 12.630 | 0 |

Salida real de la suite completa (extracto):

```text
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\mallq\OneDrive\Desktop\proyecto_ventas\puntoventa_total\.venv\Scripts\python.exe
collecting ... collected 34 items
============================= 34 passed in 5.53s ==============================
```

Auditoría real (extracto):

```text
============================== 1 passed in 2.11s ==============================
E   Failed: DID NOT RAISE PagoInsuficiente
============================== 1 failed in 3.66s ==============================
```

El fallo del mutante es intencional y constituye la evidencia de detección.

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

**Ruta: `scripts/qa_semana9_auditoria.py`**

```python
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
```

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

**R (Retorno):** «En esta medición local, completa tardó 16.469 s de pared y Core/Fast 14.116 s: diferencia 2.353 s (14.3% respecto a completa). Es una observación de un universo de 34 casos, no una predicción del ahorro total de CI. El orden, las cachés y la carga del equipo influyen; para estimar CI mediré varias repeticiones en el mismo runner y compararé medianas. Si ejecuto también la regresión completa, la prioridad mejora el tiempo hasta detectar fallos, pero no ahorra ese trabajo total.»

**E (Entorno):** «Las etiquetas permiten feedback temprano y regresión posterior, mientras los logs y JUnit hacen revisable la evidencia. El manifiesto acota el alcance: debo extender la clasificación al resto del sistema antes de llamar Core a todas sus reglas críticas. Conservar las aserciones de negocio mejora la confiabilidad de los cambios asistidos por IA.»
