import pytest

from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from tests.integration.test_rf038_050 import PASSWORD, compra
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_repositorio, construir_hasher
from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from uuid import uuid4

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def login(page, live_server, username):
    page.goto(live_server.url + "/login/")
    page.locator('[name="username"]').fill(username)
    page.locator('[name="password"]').fill(PASSWORD)
    page.get_by_role("button", name="Ingresar", exact=True).click()
    page.wait_for_url("**/catalogo/")


def test_admin_gestiona_categoria_promocion_y_consulta_reportes(navegador, live_server):
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="admin_navegador", password=PASSWORD, nombre_completo="Admin navegador", rol="ADMINISTRADOR"))
    page = navegador.new_page()
    login(page, live_server, "admin_navegador")
    page.goto(live_server.url + "/catalogo/categorias/")
    page.locator('[name="nombre"]').fill("Categoría navegador")
    page.get_by_role("button", name="Guardar categoría", exact=True).click()
    page.wait_for_url("**/catalogo/categorias/")
    categoria = CategoriaModel.objects.get(nombre="Categoría navegador")
    assert AuditoriaModel.objects.filter(entidad_id=str(categoria.id), accion="CREAR").exists()
    page.goto(live_server.url + "/promociones/crear/")
    page.locator('[name="nombre"]').fill("Porcentaje navegador")
    page.locator('[name="tipo"]').select_option("PORCENTAJE")
    page.locator('[name="descuento_valor"]').fill("10")
    page.get_by_role("button", name="Crear promocion", exact=True).click()
    page.wait_for_url("**/promociones/gestion/")
    page.get_by_role("button", name="Activar", exact=True).click()
    page.wait_for_url("**/promociones/gestion/")
    assert PromocionModel.objects.get(nombre="Porcentaje navegador").estado == "ACTIVA"
    assert page.get_by_text("Activa", exact=True).is_visible()
    page.goto(live_server.url + "/reportes/ventas/")
    assert page.get_by_role("heading", name="Métodos de pago", exact=True).is_visible()
    page.goto(live_server.url + "/reportes/productos/")
    assert page.get_by_role("heading", name="Productos más vendidos", exact=True).is_visible()


def test_cliente_consulta_su_historial_web(navegador, live_server):
    usuario = CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="cliente_historial", email="historial@example.test", password=PASSWORD,
        nombre_completo="Cliente historial", rol="CLIENTE"))
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente historial", usuario_id=usuario.id)
    venta = compra(cliente, total=37)
    page = navegador.new_page()
    login(page, live_server, "historial@example.test")
    page.goto(live_server.url + f"/clientes/historial/{cliente.id}/")
    assert page.get_by_role("heading", name="Historial de compras").is_visible()
    assert page.get_by_text(venta.numero_ticket, exact=True).is_visible()
    response = page.goto(live_server.url + "/reportes/ventas/")
    assert response.status == 200
    page.wait_for_url("**/catalogo/")
    assert "Reporte de ventas" not in page.title()


def test_admin_crea_combo_desde_selectores_de_productos(navegador, live_server):
    from tests.integration.test_pedidos_online import producto
    from src.modules.catalog.models import ProductoModel
    primero = producto()
    segundo = ProductoModel.objects.create(id=uuid4(), nombre="Jugo combo", codigo_barras="7751234567891",
                                           costo=1, precio_venta=5, estado="ACTIVO")
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="admin_combo", password=PASSWORD, nombre_completo="Admin combo", rol="ADMINISTRADOR"))
    page = navegador.new_page()
    login(page, live_server, "admin_combo")
    page.goto(live_server.url + "/promociones/crear/")
    page.locator('[name="nombre"]').fill("Desayuno navegador")
    page.locator('[name="tipo"]').select_option("COMBO")
    page.locator('[name="descuento_valor"]').fill("6")
    page.get_by_label("Producto del combo", exact=True).nth(0).select_option(str(primero.id))
    page.get_by_label("Producto del combo", exact=True).nth(1).select_option(str(segundo.id))
    page.get_by_role("button", name="Crear promocion", exact=True).click()
    page.wait_for_url("**/promociones/gestion/")
    promo = PromocionModel.objects.get(nombre="Desayuno navegador")
    assert promo.tipo == "COMBO"
    assert promo.componentes == [{"producto_id": str(primero.id), "cantidad": 1}, {"producto_id": str(segundo.id), "cantidad": 1}]


def test_admin_cancela_promocion_vencida_desde_navegador(navegador, live_server):
    from playwright.sync_api import expect

    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="admin_cancela_vencida", password=PASSWORD, nombre_completo="Admin ciclo", rol="ADMINISTRADOR"))
    promo = PromocionModel.objects.create(id=uuid4(), nombre="Vencida navegador", tipo="PORCENTAJE",
                                          estado="FINALIZADA", descuento_valor=10)
    page = navegador.new_page()
    login(page, live_server, "admin_cancela_vencida")
    page.goto(live_server.url + "/promociones/gestion/")
    fila = page.get_by_role("row").filter(has_text="Vencida navegador")
    expect(fila.get_by_text("Vencida", exact=True)).to_be_visible()
    expect(fila.get_by_role("button", name="Activar", exact=True)).to_have_count(0)
    fila.get_by_role("button", name="Cancelar", exact=True).click()
    fila = page.get_by_role("row").filter(has_text="Vencida navegador")
    expect(fila.get_by_text("Cancelada", exact=True)).to_be_visible()
    expect(fila.get_by_role("button", name="Cancelar", exact=True)).to_have_count(0)
    promo.refresh_from_db()
    assert promo.estado == "CANCELADA"


def test_cajero_cobra_con_descuento_automatico_por_frecuencia(navegador, live_server):
    from decimal import Decimal
    from tests.integration.test_pedidos_online import producto
    from src.modules.sales.models import VentaModel
    from src.modules.inventory.models import ExistenciaModel
    p = producto()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente recurrente", dni="12345678")
    compra(cliente, total=10, dias=2)
    compra(cliente, total=10, dias=1)
    PromocionModel.objects.create(id=uuid4(), nombre="Fidelidad navegador", tipo="PORCENTAJE", estado="ACTIVA",
        descuento_valor=10, aplica_clientes_frecuentes=True)
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="cajero_frecuencia", password=PASSWORD, nombre_completo="Cajero frecuencia", rol="CAJERO"))
    page = navegador.new_page()
    login(page, live_server, "cajero_frecuencia")
    page.goto(live_server.url + "/caja/apertura/")
    page.locator('[name="monto_apertura"]').fill("100")
    page.get_by_role("button", name="Abrir caja").click()
    page.wait_for_url("**/pos/")
    actual = VentaModel.objects.get(estado="BORRADOR")
    page.locator('#buscador-pos').fill(p.codigo_barras)
    with page.expect_response(lambda r: '/agregar/' in r.url) as agregado:
        page.locator('#buscador-pos').press('Enter')
    assert agregado.value.status == 200
    page.locator('[name="dni"]').fill(cliente.dni)
    page.get_by_role("button", name="Asociar cliente y calcular beneficio").click()
    page.wait_for_url("**/pago/")
    assert Decimal(page.locator('[name="monto"]').input_value()) == Decimal("1.80")
    page.locator('[name="metodo"]').select_option("EFECTIVO")
    page.locator('[name="monto_entregado"]').fill("2")
    with page.expect_response(lambda r: r.url.endswith(f'/pos/venta/{actual.id}/ticket/')) as ticket:
        page.get_by_role("button", name="Confirmar cobro").click()
    assert ticket.value.status == 200
    actual.refresh_from_db()
    assert actual.estado == "PAGADA"
    assert actual.total == Decimal("1.80")
    assert actual.cliente_id == cliente.id
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 9
