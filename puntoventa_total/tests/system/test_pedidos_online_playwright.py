"""RF-030..036 a través de Chromium y servidor Django reales, con CSRF."""
import pytest
from playwright.sync_api import expect

from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.orders.presentation.forms.pedido_form import proximo_horario_recojo
from tests.integration.test_pedidos_online import PASSWORD as PASSWORD
from tests.integration.test_pedidos_online import producto as producto
from tests.system.test_e2e_pos_playwright import navegador as navegador  # noqa: F401

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def test_cliente_se_registra_compra_y_cancela(navegador, live_server):
    p = producto()
    page = navegador.new_page()
    page.goto(live_server.url + "/clientes/registro/")
    for campo, valor in {
        "nombre": "Ana Navegador", "dni": "12345678", "email": "navegador@example.com",
        "telefono": "987654321", "password": PASSWORD, "password_confirmacion": PASSWORD,
    }.items():
        page.locator(f'[name="{campo}"]').fill(valor)
    page.get_by_role("button", name="Registrar", exact=True).click()
    page.wait_for_url("**/login/")
    page.locator('[name="username"]').fill("navegador@example.com")
    page.locator('[name="password"]').fill(PASSWORD)
    page.get_by_role("button", name="Ingresar", exact=True).click()
    page.wait_for_url("**/catalogo/")
    page.get_by_role("button", name="Agregar al carrito", exact=True).click()
    page.wait_for_url("**/pedidos/carrito/")
    assert page.get_by_text("Pan de recojo", exact=True).is_visible()
    page.goto(live_server.url + "/pedidos/checkout/")
    expect(page.locator('[name="hora_recojo"]')).to_be_disabled()
    hora_antes = proximo_horario_recojo()
    page.get_by_role("button", name="Confirmar pedido", exact=True).click()
    page.wait_for_url("**/pedidos/confirmacion/**")
    assert page.get_by_text("Pendiente", exact=True).is_visible()
    pedido = PedidoModel.objects.get()
    assert pedido.hora_recojo in (hora_antes, proximo_horario_recojo())
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 1
    page.get_by_role("button", name="Cancelar pedido", exact=True).click()
    page.wait_for_url("**/pedidos/pedido/**")
    assert page.get_by_text("Cancelado", exact=True).is_visible()
    pedido.refresh_from_db()
    assert pedido.estado == "CANCELADO"
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0
