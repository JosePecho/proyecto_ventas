"""Nivel 1 - dominio: CalculadoraVenta y value objects.

Reglas aseguradas: RN-08 (el vuelto nunca es negativo), RN-17 (redondeo
ROUND_HALF_UP a 2 decimales), desglose IGV 18% y limites de descuento de linea.
"""
from decimal import Decimal

import pytest

from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.sales.domain.exceptions.venta_exceptions import PagoInsuficiente
from src.modules.sales.domain.services.calculadora_venta import CalculadoraVenta
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _linea(cantidad: int, precio: str, pct: str = "0") -> DetalleVenta:
    linea = DetalleVenta(
        venta_id="v1",
        producto_id="p1",
        producto_nombre="Pan",
        cantidad=cantidad,
        precio_unitario=Monto(Decimal(precio)),
    )
    if Decimal(pct):
        linea.aplicar_descuento_pct(Decimal(pct))
    return linea


# --- RN-08: vuelto ---------------------------------------------------------


def test_vuelto_exacto_es_cero():
    assert CalculadoraVenta.vuelto(Monto(Decimal("10.00")), Monto(Decimal("10.00"))).valor == Decimal("0.00")


def test_vuelto_mayor_al_total_devuelve_diferencia():
    vuelto = CalculadoraVenta.vuelto(Monto(Decimal("17.50")), Monto(Decimal("20.00")))
    assert vuelto.valor == Decimal("2.50")


def test_vuelto_negativo_lanza_pago_insuficiente():
    # RN-08: entrego S/ 5.00 por una venta de S/ 10.00
    with pytest.raises(PagoInsuficiente) as exc:
        CalculadoraVenta.vuelto(Monto(Decimal("10.00")), Monto(Decimal("5.00")))
    assert exc.value.faltante == 5.0


# --- totales del carrito ---------------------------------------------------


def test_subtotal_descuentos_y_total_de_varias_lineas():
    lineas = [_linea(2, "8.50"), _linea(1, "4.00", pct="10")]
    assert CalculadoraVenta.subtotal(lineas).valor == Decimal("21.00")
    assert CalculadoraVenta.descuentos(lineas).valor == Decimal("0.40")
    assert CalculadoraVenta.total(lineas).valor == Decimal("20.60")


def test_carrito_vacio_suma_cero():
    assert CalculadoraVenta.subtotal([]).valor == Decimal("0.00")
    assert CalculadoraVenta.descuentos([]).valor == Decimal("0.00")
    assert CalculadoraVenta.total([]).valor == Decimal("0.00")


def test_total_con_descuento_adicional_de_venta():
    descuento_venta = Monto(Decimal("2.10"))
    assert CalculadoraVenta.total([_linea(1, "8.50")], descuento_venta).valor == Decimal("6.40")


# --- IGV 18% ---------------------------------------------------------------


def test_desglose_igv_de_118_sep_diez_y_ocho():
    desglose = CalculadoraVenta.desglose_igv(Monto(Decimal("118.00")))
    assert desglose["base_imponible"] == 100.0
    assert desglose["igv"] == 18.0
    assert desglose["total"] == 118.0


def test_desglose_igv_redondea_base_a_dos_decimales():
    desglose = CalculadoraVenta.desglose_igv(Monto(Decimal("9.00")))
    assert desglose["base_imponible"] == 7.63  # 9 / 1.18 = 7.6271... -> 7.63
    assert desglose["igv"] == 1.37


# --- RN-17: redondeo y validacion de Monto ---------------------------------


def test_monto_redondea_hacia_arriba_en_empate():
    assert Monto(Decimal("2.345")).valor == Decimal("2.35")  # ROUND_HALF_UP


def test_monto_redondea_hacia_abajo_bajo_el_umbral():
    assert Monto(Decimal("2.344")).valor == Decimal("2.34")


def test_monto_acepta_float_y_lo_convierte():
    assert Monto(8.5).valor == Decimal("8.50")


def test_monto_negativo_es_rechazado():
    with pytest.raises(ValidationException):
        Monto(Decimal("-0.01"))


def test_monto_rechaza_operacion_con_moneda_distinta():
    with pytest.raises(ValidationException):
        Monto(Decimal("1.00"), "PEN") + Monto(Decimal("1.00"), "USD")


def test_resta_que_dejaria_saldo_negativo_es_rechazada():
    with pytest.raises(ValidationException):
        Monto(Decimal("5.00")) - Monto(Decimal("6.00"))


# --- limites de descuento de linea -----------------------------------------


def test_descuento_de_linea_en_rango_valido_se_aplica():
    linea = _linea(2, "8.50")
    linea.aplicar_descuento_pct(Decimal("25"))
    assert linea.descuento.valor == Decimal("4.25")
    assert linea.total.valor == Decimal("12.75")


@pytest.mark.parametrize("pct", ["-1", "101"])
def test_descuento_de_linea_fuera_de_rango_es_rechazado(pct):
    with pytest.raises(ValidationException):
        _linea(1, "8.50").aplicar_descuento_pct(Decimal(pct))


@pytest.mark.parametrize("cantidad", ["0", "-3"])
def test_cantidad_invalida_en_linea_es_rechazada(cantidad):
    with pytest.raises(ValidationException):
        DetalleVenta(
            venta_id="v1",
            producto_id="p1",
            producto_nombre="Pan",
            cantidad=int(cantidad),
            precio_unitario=Monto(Decimal("8.50")),
        )


def test_cambiar_cantidad_recalcula_descuento_proporcional():
    linea = _linea(1, "10.00", pct="20")
    linea.cambiar_cantidad(3)
    assert linea.subtotal.valor == Decimal("30.00")
    assert linea.descuento.valor == Decimal("6.00")
