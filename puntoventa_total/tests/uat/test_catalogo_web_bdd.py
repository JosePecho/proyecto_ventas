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
