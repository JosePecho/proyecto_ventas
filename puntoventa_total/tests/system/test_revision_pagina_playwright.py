"""El cajero puede completar el flujo usando los controles visibles del POS."""
import pytest
from decimal import Decimal

from tests.system.test_e2e_pos_playwright import navegador, datos_pos, _login

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db]


def test_carrito_visible_cantidad_eliminacion_y_cobro(live_server, navegador, datos_pos):
    page = navegador.new_page()
    errores = []
    page.on("pageerror", lambda error: errores.append(str(error)))
    _login(page, live_server.url)
    page.goto(f"{live_server.url}/caja/apertura/")
    page.fill("[name=monto_apertura]", "100")
    page.get_by_role("button", name="Abrir caja").click()
    page.wait_for_url("**/pos/")
    page.fill("#buscador-pos", datos_pos.codigo_barras)
    page.press("#buscador-pos", "Enter")
    linea = page.locator(f'[data-producto="{datos_pos.id}"]')
    linea.wait_for()
    assert linea.locator(".cantidad").input_value() == "1"
    linea.locator(".btn-mas").click()
    page.wait_for_function("document.querySelector('.cantidad')?.value === '2'")
    linea.locator(".btn-menos").click()
    page.wait_for_function("document.querySelector('.cantidad')?.value === '1'")
    linea.locator(".btn-eliminar").click()
    page.wait_for_function("document.querySelectorAll('#lineas-carrito [data-producto]').length === 0")
    assert page.locator("#btn-cobrar").get_attribute("aria-disabled") == "true"
    page.fill("#buscador-pos", datos_pos.codigo_barras)
    page.press("#buscador-pos", "Enter")
    linea.wait_for()
    page.locator("#btn-cobrar").click()
    page.wait_for_url("**/pago/")
    assert Decimal(page.locator("[name=monto]").input_value()) == Decimal("8.50")
    page.evaluate("PV.alerta('danger', '<img src=x onerror=window.inyectado=true>')")
    assert page.locator("main .alert-danger img").count() == 0
    assert page.evaluate("window.inyectado === undefined")
    page.get_by_role("button", name="Salir", exact=True).click()
    page.wait_for_url("**/login/")
    assert not errores
