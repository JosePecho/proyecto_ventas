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
