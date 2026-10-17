"""Ciclo de atención RF-035: UI y servidor reales, con stock persistido."""
import pytest
from playwright.sync_api import expect

from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.inventory.models import ExistenciaModel
from tests.integration.test_pedidos_online import carrito, confirmar
from tests.integration.test_rf038_050 import PASSWORD
from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from tests.system.test_rf038_050_playwright import login

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def test_tienda_atiende_pedido_hasta_entrega_desde_navegador(client, navegador, live_server):
    pedido, producto = carrito(client)
    assert confirmar(client).status_code == 302
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="admin_ciclo", password=PASSWORD, nombre_completo="Administrador ciclo", rol="ADMINISTRADOR",
    ))
    page = navegador.new_page()
    login(page, live_server, "admin_ciclo")
    page.goto(live_server.url + f"/pedidos/pedido/{pedido.id}/")
    expect(page.get_by_text("Pendiente", exact=True)).to_be_visible()
    for boton, etiqueta, estado, cantidad, reservada in [
        ("Iniciar preparación", "En preparación", "EN_PREPARACION", 10, 2),
        ("Marcar listo", "Listo", "LISTO", 10, 2),
        ("Entregar pedido", "Entregado", "ENTREGADO", 8, 0),
    ]:
        page.get_by_role("button", name=boton, exact=True).click()
        expect(page.get_by_text(etiqueta, exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Cancelar pedido", exact=True)).to_have_count(0)
        pedido.refresh_from_db()
        assert pedido.estado == estado
        stock = ExistenciaModel.objects.get(producto_id=producto.id)
        assert (stock.cantidad, stock.reservada) == (cantidad, reservada)
    page.reload()
    expect(page.get_by_text("Entregado", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Entregar pedido", exact=True)).to_have_count(0)
