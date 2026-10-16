# 1. DIAGNÓSTICO ARQUITECTÓNICO Y DE TESTABILIDAD DEL MÓDULO

La repetición más reciente de los cuatro niveles se registra en
[resultado de testing](catalog_latest_results.md).

## 1.1 Lenguaje, Runtime y Framework detectado

Python 3.14.7 y Django 6.1.2 en el entorno QA existente. HTML de Django y un
script de búsqueda con debounce; las rutas son vistas HTML, no una API REST.
Se reutilizan los perfiles QA fijados en requirements/qa-inventory*.txt.
El perfil de desarrollo histórico declara otras versiones: esta prueba no
certifica todas las combinaciones de dependencias ni una instalación limpia.

## 1.2 Mapa de dependencias

| Componente | Unitarias | Integración y sistema |
|---|---|---|
| ListarProductos / FiltrarPorCategoria | Mock de ProductoRepository | DjangoProductoRepository y ORM reales |
| ConsultarDisponibilidad | Mock de DisponibilidadPort | DisponibilidadAdapter y stock real |
| Existencia y reservas | Sin BD | MySQL/InnoDB; disponible = cantidad - reservada |
| Precio e imagen | DTO real | Persistencia, storage y archivo PNG temporal servido por HTTP |
| Navegador | No se usa | Chromium con trazas y navegación anónima |
| HTTP público | No se usa | Django Client y live_server; 20 peticiones, 4 trabajadores |

## 1.3 Deuda técnica y correcciones

Se corrigieron: stock ausente en tarjetas, segunda página vacía, filtros que
ignoraban el texto, rutas de imágenes sin resolver, detalle accesible de productos
descontinuados y ausencia de Agotado en el detalle. El stock se obtiene en una
consulta en lote para evitar una consulta por tarjeta. No se cachean precios ni
cantidades en las vistas públicas; se envía Cache-Control con no-store.

Quedan como límites generales las advertencias de fechas naive/deprecaciones de
otros módulos y la configuración histórica de dependencias. No se garantiza cero
flakiness ni rendimiento con 50.000 productos a partir de esta carga pequeña.

# 2. MATRIZ DE APLICATIVOS Y HERRAMIENTAS REQUERIDAS (STACK 2026-2027)

| Nivel | Librería principal | Aplicativo / motor | Propósito | Instalación desde puntoventa_total |
|---|---|---|---|---|
| Unit | pytest 9.1.1, pytest-cov 7.1.0 | Python 3.14.7 | Paginación, filtros, DTO y disponibilidad | .venv/Scripts/python.exe -m pip install -r requirements/qa-inventory.txt |
| Integration | pytest-django 4.14.0, mysqlclient 2.3.0, PyMySQL 1.2.3 | MySQL 8.4.3 portátil o Docker y Testcontainers 4.15.0 | Persistencia y stock reales | .venv/Scripts/python.exe -m pip install -r requirements/qa-inventory-mysql.txt |
| System | Playwright 1.64.0 y urllib estándar | Chromium | UI, imagen real y carga HTTP pública | .venv/Scripts/python.exe -m playwright install chromium |
| UAT | pytest-bdd 9.0.0 | Python y BD de prueba | Cuatro escenarios de negocio | Incluido en requirements/qa-inventory.txt |

No se requieren Postman, una cuenta cloud ni servicios externos para estas vistas.
En Linux se usa `python` en lugar de `.venv/Scripts/python.exe` tras activar el entorno.

# 3. ESTRUCTURA DE DIRECTORIOS DE TESTING (SCAFFOLDING)

```text
.github/workflows/catalog-quality.yml
.cursor/rules/catalog-testing.mdc
puntoventa_total/
  tests/
    factories/catalogo_web.py
    unit/catalog/test_catalogo_web.py
    integration/test_catalogo_web.py
    system/catalog_urls.py
    system/test_catalogo_web.py
    uat/features/catalogo_web.feature
    uat/test_catalogo_web_bdd.py
  scripts/qa_inventory_mysql.py
  scripts/qa_inventory_mysql_native.py
  reports/catalog-unit-coverage.xml
  reports/catalog-load.json
  reports/catalog-regression.xml
```

# 4. NIVEL 1: PRUEBAS UNITARIAS (UNIT TESTING)

## 4.1 Qué se evalúa

Página 1/2, números negativos y fuera de rango; tamaño de página acotado; filtros
conjuntos; DTO real; stock cero/positivo y producto inexistente. No se permite ORM
en estas pruebas. Los puertos usan Mock(spec=...) y entidades reales.

## 4.2 Aplicativos y librerías

Python, pytest, pytest-cov y unittest.mock. No necesitan MySQL ni Chromium.

## 4.3 Configuración y ejecución

```powershell
.venv/Scripts/python.exe -m pip install -r requirements/qa-inventory.txt
.venv/Scripts/python.exe -m pytest tests/unit/catalog -q --cov=src.modules.catalog.application.use_cases.listar_productos --cov=src.modules.catalog.application.use_cases.filtrar_por_categoria --cov=src.modules.catalog.application.use_cases.consultar_disponibilidad --cov=src.modules.catalog.application.dto.producto_output --cov-fail-under=80 --cov-report=xml:reports/catalog-unit-coverage.xml
```

Resultado: 13 aprobadas y 100 % de líneas en esos cuatro archivos. Esta medida
no representa la cobertura de todo el módulo catalog ni una cobertura de ramas.

## 4.4 Código completo

Archivo: `tests/unit/catalog/test_catalogo_web.py`

```python
from unittest.mock import Mock

import pytest

from src.modules.catalog.application.use_cases.listar_productos import ListarProductos
from src.modules.catalog.application.use_cases.filtrar_por_categoria import FiltrarPorCategoria
from src.modules.catalog.application.use_cases.consultar_disponibilidad import ConsultarDisponibilidad
from src.modules.catalog.application.ports.disponibilidad_port import DisponibilidadPort
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoNoEncontrado

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("pagina,esperada,offset", [(1, 1, 0), (2, 2, 20), (-1, 1, 0), (999, 3, 40)])
def test_paginacion_se_resuelve_en_repositorio(producto_faker, pagina, esperada, offset):
    repo = Mock(spec=ProductoRepository)
    repo.contar.return_value = 41
    repo.listar.return_value = [producto_faker()]
    resultado = ListarProductos(repo).ejecutar(pagina=pagina, termino="arroz", categoria_id="categoria")
    assert resultado.pagina == esperada
    assert len(resultado.items) == 1
    repo.listar.assert_called_once_with(incluir_inactivos=False, termino="arroz", categoria_id="categoria", limit=20, offset=offset)
    repo.contar.assert_called_once_with(incluir_inactivos=False, termino="arroz", categoria_id="categoria")


@pytest.mark.parametrize("tamano,esperado", [(0, 1), (-10, 1), (20, 20), (999, 100)])
def test_tamano_de_pagina_acotado(tamano, esperado):
    repo = Mock(spec=ProductoRepository)
    repo.contar.return_value = 0
    repo.listar.return_value = []
    pagina = ListarProductos(repo).ejecutar(pagina=99, por_pagina=tamano)
    assert pagina.pagina == 1 and pagina.total_paginas == 1
    assert pagina.por_pagina == esperado and not pagina.items


def test_filtro_categoria_utiliza_paginacion_completa():
    repo = Mock(spec=ProductoRepository)
    repo.contar.return_value = 45
    repo.listar.return_value = []
    FiltrarPorCategoria(repo).ejecutar("bebidas", pagina=2)
    assert repo.listar.call_args.kwargs["offset"] == 20
    assert repo.listar.call_args.kwargs["categoria_id"] == "bebidas"


@pytest.mark.parametrize("stock", [0, 1, 7])
def test_disponibilidad_actual_y_agotado(producto_faker, stock):
    repo, puerto = Mock(spec=ProductoRepository), Mock(spec=DisponibilidadPort)
    producto = producto_faker()
    repo.buscar_por_id.return_value = producto
    puerto.stock_disponible.return_value = stock
    puerto.tiene_stock_minimo.return_value = stock < 5
    resultado = ConsultarDisponibilidad(repo, puerto).ejecutar(str(producto.id))
    assert resultado["stock_disponible"] == stock
    assert resultado["vendible"] == (stock > 0)


def test_detalle_inexistente_rechazado_sin_consultar_stock():
    repo, puerto = Mock(spec=ProductoRepository), Mock(spec=DisponibilidadPort)
    repo.buscar_por_id.return_value = None
    with pytest.raises(ProductoNoEncontrado):
        ConsultarDisponibilidad(repo, puerto).ejecutar("inexistente")
    puerto.stock_disponible.assert_not_called()
```

# 5. NIVEL 2: PRUEBAS DE INTEGRACIÓN (INTEGRATION TESTING)

## 5.1 Qué se evalúa

Acceso anónimo, RF-025..029, stock tras una salida de venta, precio actualizado,
cinco categorías, búsqueda, paginación 20/3, UUID inválidos, productos ocultos,
HTML escapado, URL del storage y una sola consulta de existencias para 20 tarjetas.

## 5.2 Aplicativos y librerías

pytest-django con ORM real. Se conserva Testcontainers para CI; el equipo local
dispone de MySQL nativo desechable para evitar el bloqueo de virtualización.
No se reemplaza la base de datos por mocks.

## 5.3 Configuración y ejecución

SQLite, para iterar sobre los casos del catálogo:

```powershell
.venv/Scripts/python.exe -m pytest tests/integration/test_catalogo_web.py -q
```

Los cuatro niveles y todos los módulos sobre MySQL real, sin omisiones:

```powershell
$qaMysql = Join-Path $env:TEMP 'qa-mysql-binaries/mysql-8.4.3-winx64'
.venv/Scripts/python.exe -m pip install -r requirements/qa-inventory-mysql.txt
.venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir $qaMysql --full
```

El directorio de binarios ya está preparado en este equipo. En otro equipo se
debe extraer el ZIP oficial y ajustar --basedir. El runner crea datos y credenciales
temporales, escucha en loopback, apaga y elimina su instancia. Su fixture de zonas
horarias abarca UTC y America/Lima en fechas actuales; no valida todo el historial.

Alternativa Docker para ejecutar solo el catálogo:

```powershell
docker info
.venv/Scripts/python.exe scripts/qa_inventory_mysql.py tests/integration/test_catalogo_web.py
```

## 5.4 Código completo

Archivo: `tests/factories/catalogo_web.py`

```python
from datetime import date
from uuid import uuid4

from src.modules.catalog.models import CategoriaModel, ProductoModel
from src.modules.inventory.models import ExistenciaModel, LoteModel

CATEGORIAS = [("Abarrotes", "abarrotes"), ("Bebidas", "bebidas"), ("Snacks", "snacks"),
              ("Limpieza", "limpieza"), ("Cuidado personal", "cuidado-personal")]


def categoria(nombre="Bebidas", slug="bebidas"):
    return CategoriaModel.objects.get_or_create(slug=slug, defaults={"id": uuid4(), "nombre": nombre})[0]


def producto(nombre="Agua mineral", cantidad=5, reservada=0, **kwargs):
    datos = dict(id=uuid4(), nombre=nombre, descripcion="Botella de agua mineral", estado="ACTIVO",
                 codigo_barras=f"{uuid4().int % 10**13:013d}", costo=5, precio_venta=10,
                 categoria=categoria(), stock_minimo=0)
    datos.update(kwargs)
    p = ProductoModel.objects.create(**datos)
    if cantidad is not None:
        ExistenciaModel.objects.create(id=uuid4(), producto_id=p.id, cantidad=cantidad, reservada=reservada)
        if cantidad:
            LoteModel.objects.create(id=uuid4(), producto_id=p.id, numero_lote=uuid4().hex,
                                    cantidad_inicial=cantidad, cantidad_restante=cantidad, fecha_recepcion=date.today())
    return p
```

Archivo: `tests/integration/test_catalogo_web.py`

```python
from uuid import uuid4

import pytest
from django.core.files.storage import default_storage
from django.db import connection
from django.test.utils import CaptureQueriesContext

from tests.factories.catalogo_web import CATEGORIAS, categoria, producto
from src.modules.catalog.models import ProductoModel
from src.modules.sales.infrastructure.adapters.inventario_adapter import InventarioAdapter

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_rf025_publico_precio_y_disponible_sin_autenticacion(client):
    p = producto(cantidad=8, reservada=3)
    respuesta = client.get('/catalogo/')
    assert respuesta.status_code == 200
    item = next(i for i in respuesta.context['items'] if i.id == str(p.id))
    assert item.precio_venta == 10 and item.stock_disponible == 5
    assert 'Disponible: 5 u.' in respuesta.content.decode()
    assert 'no-store' in respuesta.headers['Cache-Control']


def test_rf025_stock_y_precio_se_actualizan_tras_venta(client):
    p = producto(cantidad=2)
    assert client.get('/catalogo/').context['items'][0].stock_disponible == 2
    InventarioAdapter().descontar(str(p.id), 2, 'VENTA:CATALOGO')
    ProductoModel.objects.filter(pk=p.id).update(precio_venta=12)
    respuesta = client.get('/catalogo/')
    assert respuesta.context['items'][0].stock_disponible == 0
    assert respuesta.context['items'][0].precio_venta == 12
    assert 'Agotado' in respuesta.content.decode()
    detalle = client.get(f'/catalogo/productos/{p.id}/')
    assert detalle.context['disponibilidad']['stock_disponible'] == 0
    assert 'Agotado' in detalle.content.decode()


@pytest.mark.parametrize('nombre,slug', CATEGORIAS)
def test_rf026_cinco_categorias_filtran_y_conservan_busqueda(client, nombre, slug):
    c = categoria(nombre, slug)
    elegido = producto(nombre='Producto especial', categoria=c)
    producto(nombre='Otro producto', categoria=c)
    producto(nombre='Producto especial externo', categoria=categoria('Otra', 'otra'))
    respuesta = client.get('/catalogo/', {'categoria': str(c.id), 'q': 'especial'})
    assert [i.id for i in respuesta.context['items']] == [str(elegido.id)]
    assert f'name="categoria" value="{c.id}"' in respuesta.content.decode()


@pytest.mark.parametrize('termino', ['agua', 'AGUA', '  agua  ', 'mineral'])
def test_rf027_busqueda_nombre_parcial_y_mayusculas(client, termino):
    p = producto()
    producto(nombre='Galletas', descripcion='Galletas dulces')
    assert [i.id for i in client.get('/catalogo/', {'q': termino}).context['items']] == [str(p.id)]


def test_rf027_sin_resultados_y_texto_malicioso_escapado(client):
    producto()
    respuesta = client.get('/catalogo/', {'q': '<script>alert(1)</script>'})
    assert respuesta.status_code == 200 and not respuesta.context['items']
    assert b'<script>alert(1)</script>' not in respuesta.content
    assert 'No hay productos' in respuesta.content.decode()


def test_rf028_descripcion_imagen_precio_y_stock(client):
    p = producto(imagen='products/agua.png', cantidad=9, reservada=2)
    respuesta = client.get(f'/catalogo/productos/{p.id}/')
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert p.descripcion in html and '7 u.' in html and 'S/ 10' in html
    assert default_storage.url('products/agua.png') in html
    assert default_storage.url('products/agua.png') in client.get('/catalogo/').content.decode()
    assert 'no-store' in respuesta.headers['Cache-Control']


@pytest.mark.parametrize('cantidad,reservada', [(0, 0), (None, 0), (3, 3)])
def test_rf029_agotado_en_listado_y_detalle(client, cantidad, reservada):
    p = producto(cantidad=cantidad, reservada=reservada)
    assert 'Agotado' in client.get('/catalogo/').content.decode()
    respuesta = client.get(f'/catalogo/productos/{p.id}/')
    assert 'Agotado' in respuesta.content.decode()
    assert not respuesta.context['disponibilidad']['vendible']


@pytest.mark.parametrize('estado,activo', [('DESCONTINUADO', True), ('ACTIVO', False)])
def test_productos_no_publicos_no_se_listan_ni_abren(client, estado, activo):
    p = producto(estado=estado, activo=activo)
    assert not client.get('/catalogo/').context['items']
    assert client.get(f'/catalogo/productos/{p.id}/').status_code == 404


@pytest.mark.parametrize('pagina', ['', 'abc', '-1', '0', '9999999999999999999999999'])
def test_pagina_invalida_no_produce_500(client, pagina):
    producto()
    respuesta = client.get('/catalogo/', {'pagina': pagina})
    assert respuesta.status_code == 200 and respuesta.context['pagina'] == 1


def test_paginacion_segunda_pagina_conserva_filtros(client):
    c = categoria()
    for numero in range(23):
        producto(nombre=f'Agua {numero:02d}', categoria=c)
    primera = client.get('/catalogo/', {'q': 'Agua', 'categoria': str(c.id)})
    segunda = client.get('/catalogo/', {'q': 'Agua', 'categoria': str(c.id), 'pagina': 2})
    assert len(primera.context['items']) == 20 and len(segunda.context['items']) == 3
    assert not ({p.id for p in primera.context['items']} & {p.id for p in segunda.context['items']})
    assert f'categoria={c.id}' in primera.content.decode() and 'q=Agua' in primera.content.decode()
    assert 'pagina=2' in primera.content.decode()


def test_parametros_inexistentes_y_detalle_404(client):
    assert client.get('/catalogo/', {'categoria': 'no-es-uuid'}).status_code == 404
    assert not client.get('/catalogo/', {'categoria': str(uuid4())}).context['items']
    assert client.get(f'/catalogo/productos/{uuid4()}/').status_code == 404


def test_consulta_stock_en_lote_evitala_n_mas_uno(client):
    for numero in range(20):
        producto(nombre=f'Producto {numero}')
    with CaptureQueriesContext(connection) as consultas:
        respuesta = client.get('/catalogo/')
    assert respuesta.status_code == 200 and len(respuesta.context['items']) == 20
    stock = [q for q in consultas if 'inventory_existencia' in q['sql']]
    assert len(stock) == 1
```

# 6. NIVEL 3: PRUEBAS DE SISTEMA (SYSTEM / E2E & PERFORMANCE)

## 6.1 Qué se evalúa

Cliente anónimo: filtrar, buscar, abrir detalle y cargar un PNG real. Otro flujo
vende la última unidad, recarga y verifica Agotado en listado y detalle. La carga
ejecuta 20 GET públicos con cuatro trabajadores y exige p95 <= 2.000 ms.
La integración comprueba entradas maliciosas escapadas y detalle oculto con 404.

## 6.2 Aplicativos y librerías

Playwright/Chromium, servidor HTTP Django real y urllib/ThreadPoolExecutor. Las
trazas se guardan en reports/browser. El servidor de imágenes de tests no modifica
las rutas de medios de producción ni configura nginx.

## 6.3 Configuración y ejecución

```powershell
.venv/Scripts/python.exe -m playwright install chromium
$env:QA_REQUIRE_BROWSER = '1'
.venv/Scripts/python.exe -m pytest tests/system/test_catalogo_web.py -q
.venv/Scripts/python.exe -m pytest tests/system/test_catalogo_web.py -k carga_publica -q
```

## 6.4 Código completo de E2E y carga

Archivo: `tests/system/catalog_urls.py`

```python
"""Servicio de medios exclusivamente para las pruebas de navegador."""
from django.conf import settings
from django.urls import re_path
from django.views.static import serve
from config.urls import urlpatterns as application_urls

urlpatterns = [*application_urls, re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
```

Archivo: `tests/system/test_catalogo_web.py`

```python
import base64
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
from urllib.request import urlopen

import pytest
from django.core.files.base import ContentFile
from playwright.sync_api import expect

from tests.factories.catalogo_web import categoria, producto
from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from src.modules.sales.infrastructure.adapters.inventario_adapter import InventarioAdapter

pytestmark = [pytest.mark.system, pytest.mark.django_db(transaction=True)]


def test_cliente_anonimo_filtra_busca_y_ve_detalle_con_imagen(settings, tmp_path, live_server, navegador):
    settings.MEDIA_ROOT = tmp_path
    settings.ROOT_URLCONF = 'tests.system.catalog_urls'
    p = producto(cantidad=6, reservada=2)
    producto(nombre='Galletas', descripcion='Galletas', categoria=categoria('Snacks', 'snacks'))
    png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZWQAAAAASUVORK5CYII=')
    p.imagen.save('agua.png', ContentFile(png))
    page = navegador.new_page()
    page.goto(live_server.url + '/catalogo/')
    page.get_by_role('link', name='Bebidas', exact=True).click()
    expect(page.locator('.producto-card')).to_have_count(1)
    page.get_by_role('textbox', name='Buscar producto por nombre').fill('mineral')
    page.get_by_role('button', name='Buscar', exact=True).click()
    expect(page.locator('.producto-card')).to_have_count(1)
    expect(page.locator('.producto-card')).to_contain_text('Disponible: 4 u.')
    page.locator('.producto-card').click()
    expect(page.get_by_role('heading', name='Agua mineral')).to_be_visible()
    expect(page.locator('main')).to_contain_text('Botella de agua mineral')
    expect(page.locator('main')).to_contain_text('4 u.')
    image = page.get_by_role('img', name='Agua mineral', exact=True)
    expect(image).to_be_visible()
    expect(image).to_have_js_property('naturalWidth', 1)


def test_stock_cambia_a_agotado_al_recargar_el_catalogo(live_server, navegador):
    p = producto(cantidad=1)
    page = navegador.new_page()
    page.goto(live_server.url + '/catalogo/')
    expect(page.locator('.producto-card')).to_contain_text('Disponible: 1 u.')
    InventarioAdapter().descontar(str(p.id), 1, 'VENTA:UI-CATALOGO')
    page.reload()
    expect(page.locator('.producto-card')).to_contain_text('Agotado')
    page.locator('.producto-card').click()
    expect(page.locator('main')).to_contain_text('Agotado')


@pytest.mark.performance
def test_carga_publica_catalogo(live_server):
    producto()
    url = live_server.url.replace('localhost', '127.0.0.1') + '/catalogo/'

    def consultar(_):
        inicio = time.perf_counter()
        with urlopen(url, timeout=10) as respuesta:
            assert respuesta.status == 200
            assert 'Agua mineral' in respuesta.read().decode()
        return (time.perf_counter() - inicio) * 1000

    with ThreadPoolExecutor(max_workers=4) as pool:
        tiempos = sorted(pool.map(consultar, range(20)))
    resultado = {'usuarios': 4, 'peticiones': 20, 'p95_ms': round(tiempos[18], 2), 'limite_ms': 2000}
    Path('reports').mkdir(exist_ok=True)
    Path('reports/catalog-load.json').write_text(json.dumps(resultado), encoding='utf-8')
    assert resultado['p95_ms'] <= resultado['limite_ms'], resultado
```

# 7. NIVEL 4: PRUEBAS DE ACEPTACIÓN (UAT / BDD)

## 7.1 Escenarios de negocio

Archivo: `tests/uat/features/catalogo_web.feature`

```gherkin
Feature: Catalogo publico actualizado
  El cliente consulta productos sin iniciar sesion.

  Scenario: Consultar precio y disponibilidad
    Given un catalogo con agua en Bebidas y galletas en Snacks
    When consulta el catalogo publico
    Then ve Agua mineral con precio y 5 unidades disponibles

  Scenario: Combinar categoria y busqueda por nombre
    Given un catalogo con agua en Bebidas y galletas en Snacks
    When filtra Bebidas y busca mineral
    Then solo aparece Agua mineral

  Scenario: Consultar el detalle del producto
    Given un catalogo con agua en Bebidas y galletas en Snacks
    When abre el detalle de Agua mineral
    Then ve descripcion precio imagen y stock del producto

  Scenario: Mantener visible un producto agotado
    Given un catalogo con agua en Bebidas y galletas en Snacks
    And se vende toda el agua disponible
    When consulta el catalogo publico
    Then Agua mineral aparece como Agotado
```

## 7.2 Automatización y revisión humana

Archivo: `tests/uat/test_catalogo_web_bdd.py`

```python
import pytest
from pytest_bdd import given, when, then, scenarios

from tests.factories.catalogo_web import categoria, producto
from src.modules.sales.infrastructure.adapters.inventario_adapter import InventarioAdapter

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios('features/catalogo_web.feature')


@given('un catalogo con agua en Bebidas y galletas en Snacks', target_fixture='catalogo')
def catalogo(client):
    agua = producto(imagen='products/agua.png')
    producto(nombre='Galletas', descripcion='Galletas de chocolate', categoria=categoria('Snacks', 'snacks'))
    return {'client': client, 'agua': agua}


@when('consulta el catalogo publico')
def consultar(catalogo):
    catalogo['respuesta'] = catalogo['client'].get('/catalogo/')
    assert catalogo['respuesta'].status_code == 200


@when('filtra Bebidas y busca mineral')
def filtrar(catalogo):
    catalogo['respuesta'] = catalogo['client'].get('/catalogo/', {'q': 'mineral', 'categoria': str(catalogo['agua'].categoria_id)})


@when('abre el detalle de Agua mineral')
def detalle(catalogo):
    catalogo['respuesta'] = catalogo['client'].get(f'/catalogo/productos/{catalogo["agua"].id}/')


@given('se vende toda el agua disponible')
def agotar(catalogo):
    InventarioAdapter().descontar(str(catalogo['agua'].id), 5, 'VENTA:BDD-CATALOGO')


@then('ve Agua mineral con precio y 5 unidades disponibles')
def disponibilidad(catalogo):
    item = next(p for p in catalogo['respuesta'].context['items'] if p.id == str(catalogo['agua'].id))
    assert item.precio_venta == 10 and item.stock_disponible == 5
    assert 'Disponible: 5 u.' in catalogo['respuesta'].content.decode()


@then('solo aparece Agua mineral')
def solo_agua(catalogo):
    assert [p.nombre for p in catalogo['respuesta'].context['items']] == ['Agua mineral']


@then('ve descripcion precio imagen y stock del producto')
def verificar_detalle(catalogo):
    respuesta = catalogo['respuesta']
    assert respuesta.status_code == 200 and respuesta.context['producto'].precio_venta == 10
    assert respuesta.context['disponibilidad']['stock_disponible'] == 5
    assert 'products/agua.png' in respuesta.content.decode()
    assert 'Botella de agua mineral' in respuesta.content.decode()


@then('Agua mineral aparece como Agotado')
def agotado(catalogo):
    item = next(p for p in catalogo['respuesta'].context['items'] if p.id == str(catalogo['agua'].id))
    assert item.stock_disponible == 0 and 'Agotado' in catalogo['respuesta'].content.decode()
```

Checklist del responsable: navegar sin sesión, comprobar las cinco categorías,
buscar un nombre, abrir detalle e imagen, verificar precio, agotar un producto y
recargar. Confirmar que las reservas reducen el stock ofrecido y que los filtros
se conservan al paginar. Registrar responsable, fecha, versión y decisión.
La aprobación humana no se atribuye al resultado de pytest.

## 7.3 Ejecución y aprobación

```powershell
.venv/Scripts/python.exe -m pytest tests/uat/test_catalogo_web_bdd.py -q
```

Los escenarios automatizados requieren exit 0. El responsable firma su revisión
de RF-025..029 por separado; no se fabricó esa firma.

# 8. GUÍA DE AI SKILLS, MCP Y AUTOMATIZACIÓN AGÉNTICA (CONTEXTO 2026-2027)

## 8.1 Regla para el agente

Archivo: `.cursor/rules/catalog-testing.mdc`

```markdown
---
description: Reglas de implementacion y pruebas del catalogo publico RF-025 a RF-029
globs: puntoventa_total/src/modules/catalog/**,puntoventa_total/templates/catalog/**
alwaysApply: false
---

Leer docs/requirements/catalogo_web_rf025_rf029.md y docs/testing/catalog_master_plan.md.
Preservar acceso anonimo a /catalogo/ y /catalogo/productos/<uuid>/.
El stock disponible se consulta en vivo, descuenta reservas y se obtiene en lote.
Mantener agotados visibles y excluir productos inactivos o descontinuados.
Combinar categoria y texto; conservar filtros al paginar y consultar solo la pagina.
No introducir cache de cantidades o precios sin invalidacion demostrada.
Generar regresiones en los cuatro niveles segun el comportamiento afectado.
No eliminar aserciones ni agregar skips, xfail o retries para ocultar defectos.
Ejecutar tests/unit/catalog, tests/integration/test_catalogo_web.py,
tests/system/test_catalogo_web.py y tests/uat/test_catalogo_web_bdd.py.
La cobertura se mide sobre los cuatro archivos declarados en catalog-quality.yml;
no presentarla como cobertura de todo el modulo catalog.
Reutilizar el runner MySQL efimero con --full para comprobar todos los modulos.
No publicar cambios ni modificar protecciones de GitHub por aplicar esta regla.
```

## 8.2 MCP recomendados

El [MCP oficial de Playwright](https://github.com/microsoft/playwright-mcp) permite
inspeccionar el catálogo mediante su estructura accesible. Se puede configurar en
un cliente MCP compatible; requiere Node.js 18 o posterior. La suite automática
usa Playwright para Python y no depende de este servidor opcional.

```json
{"mcpServers":{"playwright":{"command":"npx","args":["@playwright/mcp@latest"]}}}
```

Revisar y fijar una versión del paquete antes de compartir esta configuración.
El [servidor MCP oficial de GitHub](https://github.com/github/github-mcp-server)
puede consultar resultados del workflow publicado. No se conectó ni publicó por
medio de esos servidores en esta ejecución. Para datos se usa ORM sobre la BD
efímera; no hace falta dar acceso a una base productiva a un agente.

## 8.3 Flujo de reparación de tests

1. Pedir al agente que lea la regla, el RF afectado y el primer error del reporte.
2. Ejecutar el comando real del nivel fallido; distinguir contrato, producto y test.
3. Conservar una regresión que falle con el defecto y corregir su causa.
4. Repetir el caso afectado y los cuatro niveles; no usar esperas fijas ni retries.
5. Revisar el diff y adjuntar JUnit/cobertura/traza; no publicar sin autorización.

Comando reproducible para detectar fallos en los cuatro niveles:

```powershell
.venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir $qaMysql --full
```

La regla orienta al agente; no instala un servicio de reparación automática ni
autoriza cambiar requisitos para hacer pasar una prueba.

# 9. PIPELINE CI/CD (QUALITY GATES)

Cuatro jobs secuenciales: Unit -> Integration -> System -> UAT. Cobertura mínima
80 % en los cuatro archivos declarados; BD MySQL efímera; Chromium obligatorio.
El archivo se encuentra en .github/workflows de la raíz, no dentro de la aplicación.
Exigir los cuatro checks Catalog / Unit, Integration, System y UAT en las reglas
de rama para bloquear merges. El YAML por sí solo no configura esas protecciones.
La ejecución remota no se presenta como observada.

Archivo: `.github/workflows/catalog-quality.yml`

```yaml
name: Catalog quality

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: catalog-${{ github.ref }}
  cancel-in-progress: true

defaults:
  run:
    working-directory: puntoventa_total

jobs:
  unit:
    name: Catalog / Unit
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14.7'
          cache: pip
          cache-dependency-path: puntoventa_total/requirements/*.txt
      - run: python -m pip install -r requirements/qa-inventory.txt
      - run: >-
          python -m pytest tests/unit/catalog -q
          --cov=src.modules.catalog.application.use_cases.listar_productos
          --cov=src.modules.catalog.application.use_cases.filtrar_por_categoria
          --cov=src.modules.catalog.application.use_cases.consultar_disponibilidad
          --cov=src.modules.catalog.application.dto.producto_output
          --cov-fail-under=80 --cov-report=xml:reports/catalog-unit-coverage.xml
          --junitxml=reports/catalog-unit.xml
      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: catalog-unit
          path: puntoventa_total/reports/

  integration:
    name: Catalog / Integration
    needs: unit
    runs-on: ubuntu-24.04
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14.7'
      - run: sudo apt-get update && sudo apt-get install -y pkg-config default-libmysqlclient-dev build-essential
      - run: python -m pip install -r requirements/qa-inventory-mysql.txt
      - run: >-
          python scripts/qa_inventory_mysql.py tests/integration/test_catalogo_web.py
          tests/integration/test_inventario_mysql.py --junitxml=reports/catalog-integration.xml
      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: catalog-integration
          path: puntoventa_total/reports/

  system:
    name: Catalog / System
    needs: integration
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    env:
      QA_REQUIRE_BROWSER: '1'
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14.7'
      - run: python -m pip install -r requirements/qa-inventory.txt
      - run: python -m playwright install --with-deps chromium
      - run: python -m pytest tests/system/test_catalogo_web.py -q --junitxml=reports/catalog-system.xml
      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: catalog-system
          path: puntoventa_total/reports/

  uat:
    name: Catalog / UAT
    needs: system
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14.7'
      - run: python -m pip install -r requirements/qa-inventory.txt
      - run: python -m pytest tests/uat/test_catalogo_web_bdd.py -q --junitxml=reports/catalog-uat.xml
      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: catalog-uat
          path: puntoventa_total/reports/
```

# 10. MATRIZ DE TRAZABILIDAD DE PRUEBAS DEL MÓDULO

| ID caso | Funcionalidad | Nivel | Tipo | Resultado esperado | Ejecución |
|---|---|---|---|---|---|
| CAT-U01 | ListarProductos y FiltrarPorCategoria | Unit | Borde | Offset, página y filtros correctos | python -m pytest tests/unit/catalog -q |
| CAT-I25 | RF-025 catálogo vigente | Int | Positivo | Precio y disponible actualizados tras venta | python -m pytest tests/integration/test_catalogo_web.py -k rf025 -q |
| CAT-I26 | RF-026 cinco categorías | Int | Positivo | Solo categoría y texto elegidos | python -m pytest tests/integration/test_catalogo_web.py -k rf026 -q |
| CAT-I27 | RF-027 búsqueda | Int | Positivo/Negativo | Parcial, mayúsculas, vacío y HTML seguro | python -m pytest tests/integration/test_catalogo_web.py -k rf027 -q |
| CAT-I28 | RF-028 detalle | Int | Positivo | Imagen URL, descripción, precio y stock | python -m pytest tests/integration/test_catalogo_web.py -k rf028 -q |
| CAT-I29 | RF-029 Agotado | Int | Borde | Cero, sin existencia y todo reservado | python -m pytest tests/integration/test_catalogo_web.py -k rf029 -q |
| CAT-I30 | Paginación y consulta en lote | Int | Borde | 20/3 productos sin duplicados; un SELECT de existencias | python -m pytest tests/integration/test_catalogo_web.py -q |
| CAT-S01 | Cliente anónimo y stock actualizado | Sys | Positivo | Flujo visible, imagen cargada y Agotado tras recarga | python -m pytest tests/system/test_catalogo_web.py -q |
| CAT-P01 | Carga pública | Sys | Positivo | 20 respuestas válidas, p95 <=2000 ms | python -m pytest tests/system/test_catalogo_web.py -k carga_publica -q |
| CAT-A01..04 | Cuatro escenarios de negocio | UAT | Positivo/Borde | Criterios RF satisfechos | python -m pytest tests/uat/test_catalogo_web_bdd.py -q |

# EVALUACIÓN FINAL DEL MÓDULO AUDITADO

Valoraciones de ingeniería, no certificaciones externas:

| Dimensión | Puntuación | Evidencia / límite |
|---|---|---|
| Testabilidad | 8/10 | Puertos aislables, vistas y storage probados con infraestructura |
| Cobertura unitaria alcanzable | 9/10 | 100 % medido en los cuatro archivos de aplicación seleccionados |
| Aislamiento | 8/10 | Sin ORM en unitarias; BD real en otros niveles |
| Preparación CI/CD | 8/10 | Workflow y gates implementados; ejecución remota no observada |
| Resiliencia | 8/10 | Límites, stock cero, UUID inválidos, XSS, filtros y concurrencia del inventario |

# ESTADO DE CALIDAD (QUALITY READINESS)

| Nivel | Estado |
|---|---|
| Unit Test Ready | Listo; 13 pruebas y cobertura del alcance declarado |
| Integration Ready | Listo; 26 casos del catalogo aprobados en MySQL real |
| System / E2E Ready | Navegador e imagen real ejecutados; carga pequeña, no productiva |
| UAT / Business Ready | Cuatro escenarios BDD aprobados en MySQL; aprobacion humana separada |

## Evidencia final observada

Ejecucion: 2026-10-16T21:02:56.500689+00:00. Python 3.14.7 / Django 6.1.2 / MySQL
8.4.3 InnoDB nativo efimero, Chromium obligatorio.

| Comprobacion | Resultado |
|---|---|
| Regresion completa | 346 aprobadas; 0 fallos, 0 errores, 0 omisiones, 0 xfail |
| Catalogo nuevo | 46 casos: 13 unitarios, 26 de integracion, 3 de sistema y 4 BDD |
| Cobertura unitaria seleccionada | 100.00 % de lineas de los cuatro archivos declarados |
| Carga publica | 20 peticiones, 4 trabajadores, sin errores; p95 333.54 ms <= 2000 ms |
| Migraciones | makemigrations catalog --check --dry-run: sin cambios pendientes |
| CI remoto | Workflow escrito; no publicado ni ejecutado en GitHub Actions |
| Aceptacion humana | Checklist entregado; no se atribuye aprobacion al cliente |

Artefactos: reports/catalog-regression.xml/json, catalog-unit-coverage.xml/json,
catalog-load.json y browser/*.zip. La instancia temporal se apago y elimino.
Se emitieron 24 advertencias existentes, sin fallos de la suite. La ruta
Docker/Testcontainers no se ejecuto localmente; se verifico el motor real nativo.
