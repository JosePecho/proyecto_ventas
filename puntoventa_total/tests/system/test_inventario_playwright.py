"""Flujo de almacen en Chromium: producto, recepcion, merma, alertas y reportes."""
import uuid
from datetime import date, timedelta

import pytest

from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from src.modules.catalog.models import CategoriaModel, ProductoModel
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db]


def test_almacenero_completa_flujo_de_inventario(live_server, navegador):
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
        UsuarioInputDTO(nombre_completo="Almacenero UI", username="almacen_ui", email="almacen_ui@example.test",
                        password="Secreta123", rol=RolUsuario.ALMACENERO.value)
    )
    categoria = CategoriaModel.objects.create(id=uuid.uuid4(), nombre="Lacteos UI", slug="lacteos-ui")
    vencimiento = (date.today() + timedelta(days=20)).isoformat()
    page = navegador.new_page()
    page.goto(live_server.url)
    page.fill("input[name=username]", "almacen_ui")
    page.fill("input[name=password]", "Secreta123")
    page.click("button:has-text('Ingresar')")
    page.wait_for_url("**/catalogo/")

    page.goto(f"{live_server.url}/inventario/")
    page.get_by_role("link", name="Registrar producto", exact=True).click()
    page.fill("input[name=nombre]", "Leche UI")
    page.fill("input[name=codigo_barras]", "7751234567811")
    page.fill("input[name=costo]", "5")
    page.fill("input[name=precio_venta]", "8")
    page.select_option("select[name=categoria_id]", str(categoria.id))
    page.fill("input[name=stock_minimo]", "8")
    page.fill("input[name=fecha_vencimiento]", vencimiento)
    page.get_by_role("button", name="Guardar", exact=True).click()
    page.wait_for_url("**/catalogo/productos/admin/")
    producto = ProductoModel.objects.get(codigo_barras="7751234567811")
    assert producto.stock_minimo == 8 and producto.categoria_id == categoria.id

    page.goto(f"{live_server.url}/inventario/recepcion/")
    page.select_option("select[name=producto_id]", str(producto.id))
    page.fill("input[name=numero_lote]", "LOTE-UI")
    page.fill("input[name=cantidad]", "10")
    page.fill("input[name=costo_unitario]", "5")
    page.fill("input[name=fecha_vencimiento]", vencimiento)
    page.get_by_role("button", name="Registrar ingreso", exact=True).click()
    page.wait_for_url("**/inventario/")
    assert ExistenciaModel.objects.get(producto_id=producto.id).cantidad == 10
    lote = LoteModel.objects.get(producto_id=producto.id)

    page.get_by_role("link", name="Registrar merma", exact=True).click()
    page.select_option("select[name=producto_id]", str(producto.id))
    page.select_option("select[name=lote_id]", str(lote.id))
    page.fill("input[name=cantidad]", "3")
    page.select_option("select[name=motivo]", "DANADO")
    page.get_by_role("button", name="Registrar merma", exact=True).click()
    page.wait_for_load_state("networkidle")
    assert ExistenciaModel.objects.get(producto_id=producto.id).cantidad == 7
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 7

    page.goto(f"{live_server.url}/inventario/alertas/")
    assert "Leche UI: 7 u." in page.content()
    assert "LOTE-UI" in page.content()
    page.goto(f"{live_server.url}/inventario/kardex/?producto_id={producto.id}")
    assert "ENTRADA" in page.content() and "MERMA" in page.content()
    assert MovimientoModel.objects.filter(producto_id=producto.id).count() == 2
    page.goto(f"{live_server.url}/reportes/inventario/")
    assert "Leche UI" in page.content() and "60 dias" in page.content()
    assert "Mayor ganancia por producto" in page.content()
