from datetime import timedelta
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_bdd import given, when, then, scenarios

from tests.integration.test_rf038_050 import staff, compra, promo_payload
from tests.integration.test_pedidos_online import producto
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.promotions.infrastructure.factories import construir_promocion_repository
from src.modules.promotions.application.use_cases.calcular_descuento import CalcularDescuento
from src.modules.promotions.infrastructure.tasks.actualizar_estado_promociones import run
from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios("features/clientes_promociones_admin.feature")


@pytest.fixture
def contexto():
    return {}


@given("un cajero autenticado")
def cajero(client, contexto):
    contexto["usuario"] = staff(client, "CAJERO")


@given("un administrador autenticado")
def administrador(client, contexto):
    contexto["usuario"] = staff(client)


@when("registra el DNI y teléfono del cliente")
def registra(client):
    assert client.post(reverse("customers:registro"), {"nombre": "Cliente UAT", "dni": "12345678", "telefono": "987654321"}).status_code == 302


@then("el cliente frecuente queda registrado sin pertenecer al cajero")
def registrado():
    cliente = ClienteModel.objects.get(dni="12345678")
    assert cliente.telefono == "987654321"
    assert cliente.usuario_id is None


@given("una cliente con dos compras pagadas y una anulada")
def cliente(client, contexto):
    usuario = staff(client, "CLIENTE")
    contexto["cliente"] = ClienteModel.objects.create(id=uuid4(), nombre="Cliente UAT", usuario_id=usuario.id)
    compra(contexto["cliente"], total=10, dias=1)
    compra(contexto["cliente"], total=20)
    compra(contexto["cliente"], total=999, estado="ANULADA")


@when("consulta su historial web")
def consulta(client, contexto):
    contexto["respuesta"] = client.get(reverse("customers:historial", args=[contexto["cliente"].id]))


@then("ve dos compras por un total de treinta soles")
def historial(contexto):
    assert contexto["respuesta"].status_code == 200
    assert contexto["respuesta"].context["historial"]["total_gastado"] == 30
    assert contexto["respuesta"].context["historial"]["cantidad"] == 2


@given("un administrador con un producto de dos soles")
def admin_producto(client, contexto):
    administrador(client, contexto)
    contexto["producto"] = producto()


@when("crea y activa una promoción 2x1")
def crea_2x1(client, contexto):
    assert client.post(reverse("promotions:crear"), promo_payload("NX1", producto_id=str(contexto["producto"].id), descuento_valor="0")).status_code == 302
    promocion = PromocionModel.objects.get()
    assert client.post(reverse("promotions:promociones"), {"accion": "activar", "promocion_id": str(promocion.id)}).status_code == 302


@then("dos unidades reciben dos soles de descuento")
def descuento(contexto):
    assert CalcularDescuento(construir_promocion_repository()).por_producto(str(contexto["producto"].id), Monto(4), 2).valor == 2


@given("una promoción programada cuyo periodo ya terminó")
def vencida():
    ahora = timezone.now()
    PromocionModel.objects.create(id=uuid4(), nombre="UAT vencida", tipo="PORCENTAJE", estado="PROGRAMADA", descuento_valor=10,
        vigencia_desde=ahora - timedelta(days=2), vigencia_hasta=ahora - timedelta(days=1))


@when("se actualiza la vigencia de promociones")
def actualiza():
    run()


@then("queda Vencida y no aparece entre las promociones públicas")
def no_publica(client):
    assert PromocionModel.objects.get().estado == "FINALIZADA"
    assert client.get(reverse("promotions:activas"), HTTP_ACCEPT="application/json").json()["promociones"] == []


@given("un administrador y ventas pagadas y anuladas")
def ventas(client, contexto):
    administrador(client, contexto)
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente reportes")
    compra(cliente, total=37)
    compra(cliente, total=999, estado="ANULADA")


@when("consulta el reporte de ventas")
def reporte(client, contexto):
    contexto["respuesta"] = client.get(reverse("reporting:ventas"))


@then("ve una transacción pagada y su método de pago")
def reporte_correcto(contexto):
    respuesta = contexto["respuesta"]
    assert respuesta.status_code == 200
    assert respuesta.context["reporte"].total_ventas == 37
    assert respuesta.context["reporte"].cantidad_tickets == 1
    assert respuesta.context["metodos"] == {"EFECTIVO": 37}


@when("crea una categoría de productos")
def categoria(client):
    assert client.post(reverse("catalog:categorias"), {"nombre": "Categoría UAT"}).status_code == 302


@then("la auditoría identifica al administrador y la categoría creada")
def audita(contexto):
    categoria = CategoriaModel.objects.get(nombre="Categoría UAT")
    assert AuditoriaModel.objects.filter(entidad="CategoriaModel", entidad_id=str(categoria.id), usuario_id=contexto["usuario"].id, accion="CREAR").exists()


@when("intenta crear una promoción")
def intenta(client, contexto):
    contexto["respuesta"] = client.post(reverse("promotions:crear"), promo_payload())


@then("el sistema deniega la operación y no crea promociones")
def deniega(contexto):
    assert contexto["respuesta"].status_code == 302
    assert contexto["respuesta"].url == reverse("catalog:catalogo")
    assert PromocionModel.objects.count() == 0


@given("un carrito de dos soles para una cliente recurrente con fidelización vigente")
def carrito_recurrente(client, contexto):
    from src.modules.sales.domain.entities.venta import Venta
    from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
    from src.modules.sales.infrastructure.factories import construir_venta_repository
    cajero(client, contexto)
    p = producto()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Recurrente UAT", dni="12345678")
    compra(cliente, total=10, dias=2)
    compra(cliente, total=10, dias=1)
    PromocionModel.objects.create(id=uuid4(), nombre="Fidelidad UAT", tipo="PORCENTAJE", estado="ACTIVA",
        descuento_valor=10, aplica_clientes_frecuentes=True)
    agregado = VentaAggregate(Venta(numero_ticket="T-UAT-FRECUENCIA", cajero_id=contexto["usuario"].id))
    agregado.agregar_producto(str(p.id), p.nombre, 1, Monto(2))
    agregado.calcular_totales()
    construir_venta_repository().guardar(agregado)
    contexto["cliente"], contexto["venta_id"] = cliente, str(agregado.venta.id)


@when("el cajero asocia el DNI de esa cliente a la venta")
def asocia(client, contexto):
    assert client.post(reverse("sales:asignar_cliente", args=[contexto["venta_id"]]), {"dni": contexto["cliente"].dni}).status_code == 302


@then("el importe a cobrar baja automáticamente a un sol con ochenta céntimos")
def beneficio_automatico(contexto):
    from src.modules.sales.infrastructure.factories import construir_venta_repository
    venta = construir_venta_repository().buscar_por_id(contexto["venta_id"])
    assert venta.venta.total == 1.8
    assert venta.descuento_venta_pct == 10
