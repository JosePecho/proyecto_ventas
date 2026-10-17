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
