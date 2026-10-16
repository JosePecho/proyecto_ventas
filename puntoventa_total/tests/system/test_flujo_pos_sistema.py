"""Nivel 3 - Sistema: flujo completo del POS por HTTP contra la app Django.

Cubre con POST reales el hueco que dejaban vacios tests/e2e (solo GETs):
apertura de caja -> escaneo -> agregar -> cobro parcial -> cobro total ->
ticket PDF -> anulacion con devolucion de stock.

Solo inventario/auditoria externos no participan: se usan los adaptadores
reales del sistema sobre la BD de prueba (config.settings.testing).
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest

from src.modules.cash_register.infrastructure.persistence.django_models.turno_caja_model import (
    TurnoCajaModel,
)
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import (
    ProductoModel,
)
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import (
    ExistenciaModel,
)
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.persistence.django_models.movimiento_model import (
    MovimientoModel,
)
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel

pytestmark = [pytest.mark.system, pytest.mark.django_db]

CODIGO_BARRAS = "7751234567890"


@pytest.fixture
def producto_con_stock():
    producto = ProductoModel.objects.create(
        id=uuid.uuid4(),
        nombre="Arroz 1kg",
        codigo_barras=CODIGO_BARRAS,
        costo=Decimal("5.00"),       # RN-01: venta >= costo + 10%
        precio_venta=Decimal("8.50"),
        estado="ACTIVO",
        requiere_stock=True,
    )
    ExistenciaModel.objects.create(
        id=uuid.uuid4(), producto_id=producto.id, cantidad=20, reservada=0
    )
    LoteModel.objects.create(
        id=uuid.uuid4(),
        producto_id=producto.id,
        numero_lote="L-001",
        cantidad_inicial=20,
        cantidad_restante=20,
        fecha_recepcion=date.today(),
    )
    return producto


@pytest.fixture
def cajero(client, django_user_model):
    django_user_model.objects.create_user(username="cajero_sistema", password="Secreta123")
    assert client.login(username="cajero_sistema", password="Secreta123")
    sesion = client.session
    sesion["rol"] = "CAJERO"                 # lo fija el login real (login_view)
    sesion["usuario_id"] = str(uuid.uuid4())  # UUID: TurnoCajaModel exige UUIDField
    sesion.save()
    return sesion


def _abrir_caja(client, monto: str = "200.00"):
    respuesta = client.post("/caja/apertura/", {"monto_apertura": monto})
    assert respuesta.status_code == 302
    assert respuesta.url == "/pos/"
    return client.session["turno_caja_id"]


def _venta_actual(client) -> str:
    respuesta = client.get("/pos/")
    assert respuesta.status_code == 200
    return client.session["venta_actual"]


def _escanear(client) -> str:
    respuesta = client.get("/pos/buscar/", {"q": CODIGO_BARRAS})
    assert respuesta.status_code == 200
    resultados = respuesta.json()["resultados"]
    assert len(resultados) == 1
    assert resultados[0]["nombre"] == "Arroz 1kg"
    assert resultados[0]["precio"] == 8.5
    return resultados[0]["id"]


def test_flujo_completo_cobrar_y_emitir_ticket_pdf(client, producto_con_stock, cajero):
    _abrir_caja(client)
    venta_id = _venta_actual(client)
    producto_id = _escanear(client)

    # agregar 2 unidades por AJAX
    respuesta = client.post(f"/pos/venta/{venta_id}/agregar/{producto_id}/", {"cantidad": "2"})
    assert respuesta.status_code == 200
    assert respuesta.json() == {"total": 17.0, "lineas": 1}

    # los totales quedan PERSISTIDOS (regresion del fix de AgregarProducto)
    venta = VentaModel.objects.get(pk=venta_id)
    assert venta.total == Decimal("17.00")

    # cobro total con efectivo: 17.00 de 20.00 -> vuelto 3.00 (RN-08)
    respuesta = client.post(
        f"/pos/venta/{venta_id}/pago/",
        {"metodo": "EFECTIVO", "monto": "17.00", "monto_entregado": "20.00"},
    )
    assert respuesta.status_code == 302
    assert respuesta.url == f"/pos/venta/{venta_id}/ticket/"

    venta.refresh_from_db()
    assert venta.estado == "PAGADA"
    assert venta.total == Decimal("17.00")

    # el stock se desconto con PEPS y quedo trazado en el kardex
    assert ExistenciaModel.objects.get(producto_id=producto_con_stock.id).cantidad == 18
    salidas = MovimientoModel.objects.filter(producto_id=producto_con_stock.id, tipo="SALIDA_VENTA")
    assert salidas.count() == 1
    assert salidas.get().referencia == f"VENTA:{venta.numero_ticket}"

    # el ticket se emite en PDF
    ticket = client.get(f"/pos/venta/{venta_id}/ticket/")
    assert ticket.status_code == 200
    assert ticket["Content-Type"] == "application/pdf"
    assert ticket.content.startswith(b"%PDF")


def test_pago_parcial_no_cierra_la_venta(client, producto_con_stock, cajero):
    _abrir_caja(client)
    venta_id = _venta_actual(client)
    producto_id = _escanear(client)
    client.post(f"/pos/venta/{venta_id}/agregar/{producto_id}/", {"cantidad": "2"})

    respuesta = client.post(
        f"/pos/venta/{venta_id}/pago/",
        {"metodo": "EFECTIVO", "monto": "5.00", "monto_entregado": "5.00"},
    )
    assert respuesta.status_code == 302
    assert respuesta.url == f"/pos/venta/{venta_id}/pago/"  # vuelve al cobro

    venta = VentaModel.objects.get(pk=venta_id)
    assert venta.estado == "BORRADOR"  # RN-06: no cerro con pago insuficiente
    assert ExistenciaModel.objects.get(producto_id=producto_con_stock.id).cantidad == 20  # sin descuento
    assert MovimientoModel.objects.filter(producto_id=producto_con_stock.id).count() == 0


def test_no_se_puede_operar_el_pos_sin_caja_abierta(client, producto_con_stock, cajero):
    respuesta = client.get("/pos/")
    assert respuesta.status_code == 302
    assert respuesta.url == "/caja/apertura/"


def test_un_cajero_no_puede_tener_dos_turnos_abiertos(client, producto_con_stock, cajero):
    _abrir_caja(client, "100.00")

    respuesta = client.post("/caja/apertura/", {"monto_apertura": "50.00"})

    assert respuesta.status_code == 200  # vuelve a renderizar el form con error
    assert TurnoCajaModel.objects.count() == 1  # RN-09


def test_anulacion_devuelve_stock_y_es_única(client, producto_con_stock, cajero):
    _abrir_caja(client)
    venta_id = _venta_actual(client)
    producto_id = _escanear(client)
    client.post(f"/pos/venta/{venta_id}/agregar/{producto_id}/", {"cantidad": "2"})
    client.post(
        f"/pos/venta/{venta_id}/pago/",
        {"metodo": "EFECTIVO", "monto": "17.00", "monto_entregado": "17.00"},
    )

    # la anulacion exige rol GERENTE/ADMINISTRADOR
    sesion = client.session
    sesion["rol"] = "GERENTE"
    sesion.save()

    respuesta = client.post(f"/pos/venta/{venta_id}/anular/", {"motivo": "cliente se equivoco"})
    assert respuesta.status_code == 302
    assert respuesta.url == "/pos/ventas/"

    venta = VentaModel.objects.get(pk=venta_id)
    assert venta.estado == "ANULADA"
    assert venta.observacion == "cliente se equivoco"
    assert ExistenciaModel.objects.get(producto_id=producto_con_stock.id).cantidad == 20  # devuelto
    assert MovimientoModel.objects.filter(tipo="DEVOLUCION", producto_id=producto_con_stock.id).count() == 1

    # RN-06: la segunda anulacion se rechaza sin repetir la devolucion
    respuesta = client.post(f"/pos/venta/{venta_id}/anular/", {"motivo": "otra vez"})
    assert respuesta.status_code == 200
    venta.refresh_from_db()
    assert venta.estado == "ANULADA"
    assert venta.observacion == "cliente se equivoco"
    assert MovimientoModel.objects.filter(tipo="DEVOLUCION", producto_id=producto_con_stock.id).count() == 1


def test_anulacion_requiere_rol_gerente(client, producto_con_stock, cajero):
    _abrir_caja(client)
    venta_id = _venta_actual(client)

    # el cajero (rol CAJERO) no puede anular: role_required lo redirige
    respuesta = client.post(f"/pos/venta/{venta_id}/anular/", {"motivo": "intento"})
    assert respuesta.status_code == 302
    assert respuesta.url == "/catalogo/"
