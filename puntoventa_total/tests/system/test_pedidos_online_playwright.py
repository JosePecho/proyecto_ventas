"""RF-030..036 a través de Chromium y servidor Django reales, con CSRF."""
from datetime import timedelta

import pytest
from django.utils import timezone

from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from tests.integration.test_pedidos_online import PASSWORD, producto
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel

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
    hora = (timezone.localtime() + timedelta(days=1)).replace(minute=30, second=0, microsecond=0)
    page.locator('[name="hora_recojo"]').fill(hora.strftime("%Y-%m-%dT%H:%M"))
    page.get_by_role("button", name="Confirmar pedido", exact=True).click()
    page.wait_for_url("**/pedidos/confirmacion/**")
    assert page.get_by_text("Pendiente", exact=True).is_visible()
    pedido = PedidoModel.objects.get()
    assert pedido.hora_recojo == hora
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 1
    page.get_by_role("button", name="Cancelar pedido", exact=True).click()
    page.wait_for_url("**/pedidos/pedido/**")
    assert page.get_by_text("Cancelado", exact=True).is_visible()
    pedido.refresh_from_db()
    assert pedido.estado == "CANCELADO"
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0
