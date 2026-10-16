"""Nivel 1 - dominio: invariantes del agregado Venta (RN-06 y RN-07).

RN-06: una venta no puede anularse dos veces ni cerrarse sin pago total.
RN-07: el descuento total de la venta no puede superar 50%.
"""
from decimal import Decimal

import pytest

from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.pago import Pago
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.domain.exceptions.venta_exceptions import (
    PagoInsuficiente,
    ProductoYaAgregado,
    VentaException,
    VentaNoModificable,
)
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _agregado_con_linea(precio: str = "10.00", cantidad: int = 1) -> VentaAggregate:
    agregado = VentaAggregate(venta=Venta(numero_ticket="T0001", cajero_id="cajero-1"))
    agregado.agregar_producto("p1", "Pan", cantidad, Monto(Decimal(precio)))
    return agregado


def _agregado_cobrado(total: str) -> VentaAggregate:
    agregado = _agregado_con_linea(precio=total)
    agregado.calcular_totales()
    agregado.registrar_pago(Pago.efectivo("T0001", Monto(Decimal(total))))
    return agregado


# --- RN-07: tope de descuento de la venta ----------------------------------


def test_descuento_de_venta_mayor_a_50_por_ciento_es_rechazado():
    agregado = _agregado_con_linea()
    with pytest.raises(VentaException):
        agregado.aplicar_descuento_venta(Decimal("50.01"))


def test_descuento_de_venta_negativo_es_rechazado():
    with pytest.raises(VentaException):
        _agregado_con_linea().aplicar_descuento_venta(Decimal("-1"))


def test_descuento_de_venta_del_50_por_ciento_exacto_se_aplica():
    agregado = _agregado_con_linea(precio="20.00")
    agregado.aplicar_descuento_venta(Decimal("50"))
    totales = agregado.calcular_totales()
    assert totales["descuento"] == 10.0
    assert totales["total"] == 10.0


def test_descuento_de_venta_no_es_permitido_si_la_venta_no_es_borrador():
    agregado = _agregado_cobrado("20.00")
    agregado.cerrar()
    with pytest.raises(VentaNoModificable):
        agregado.aplicar_descuento_venta(Decimal("10"))


# --- RN-06: anulacion unica ------------------------------------------------


def test_no_se_puede_anular_dos_veces():
    agregado = _agregado_con_linea()
    agregado.anular("motivo uno", "gerente-1")
    assert agregado.venta.estado == EstadoVenta.ANULADA
    with pytest.raises(VentaNoModificable):
        agregado.anular("motivo dos", "gerente-1")


def test_anular_publica_evento_con_motivo_y_usuario():
    agregado = _agregado_con_linea()
    agregado.anular("cliente se equivoco", "gerente-1")
    evento = next(e for e in agregado.venta.eventos_pendientes() if e.nombre == "VentaAnulada")
    assert evento.motivo == "cliente se equivoco"
    assert evento.usuario_id == "gerente-1"


def test_requiere_devolucion_stock_solo_si_esta_anulada_con_lineas():
    agregado = _agregado_con_linea()
    assert agregado.requiere_devolucion_stock() is False
    agregado.calcular_totales()
    agregado.registrar_pago(Pago.efectivo("T0001", Monto(Decimal("10.00"))))
    agregado.cerrar()
    assert agregado.requiere_devolucion_stock() is False
    agregado.anular("cambio de opinion")
    assert agregado.requiere_devolucion_stock() is True


def test_venta_anulada_no_admite_modificar_lineas():
    agregado = _agregado_con_linea()
    agregado.anular("motivo")
    with pytest.raises(VentaNoModificable):
        agregado.modificar_cantidad("p1", 5)
    with pytest.raises(VentaNoModificable):
        agregado.eliminar_producto("p1")


# --- cobro y cierre --------------------------------------------------------


def test_registrar_pago_sin_lineas_es_rechazado():
    agregado = VentaAggregate(venta=Venta(numero_ticket="T0002", cajero_id="cajero-1"))
    with pytest.raises(VentaException):
        agregado.registrar_pago(Pago.efectivo("T0002", Monto(Decimal("10.00"))))


def test_pago_parcial_deja_saldo_pendiente():
    agregado = _agregado_con_linea(precio="10.00")
    agregado.calcular_totales()
    agregado.registrar_pago(Pago.efectivo("T0001", Monto(Decimal("4.00"))))
    assert agregado.total_pagado() == Decimal("4.00")
    assert agregado.saldo_pendiente() == Decimal("6.00")


def test_cerrar_con_pago_completo_publica_venta_pagada():
    agregado = _agregado_cobrado("10.00")
    agregado.cerrar()
    assert agregado.venta.estado == EstadoVenta.PAGADA
    assert any(e.nombre == "VentaPagada" for e in agregado.venta.eventos_pendientes())


def test_cerrar_sin_pago_total_no_cambia_estado():
    agregado = _agregado_con_linea(precio="10.00")
    agregado.calcular_totales()
    agregado.registrar_pago(Pago.efectivo("T0001", Monto(Decimal("9.99"))))
    with pytest.raises(PagoInsuficiente):
        agregado.cerrar()
    assert agregado.venta.estado == EstadoVenta.BORRADOR


# --- operaciones sobre lineas ----------------------------------------------


def test_producto_duplicado_es_rechazado():
    agregado = _agregado_con_linea()
    with pytest.raises(ProductoYaAgregado):
        agregado.agregar_producto("p1", "Pan", 1, Monto(Decimal("10.00")))


def test_modificar_cantidad_de_producto_inexistente_es_rechazado():
    with pytest.raises(VentaException):
        _agregado_con_linea().modificar_cantidad("no-existe", 2)


def test_eliminar_producto_recalcula_totales():
    agregado = _agregado_con_linea(precio="10.00")
    agregado.agregar_producto("p2", "Leche", 1, Monto(Decimal("5.00")))
    agregado.calcular_totales()
    assert agregado.venta.total == 15.0
    agregado.eliminar_producto("p2")
    totales = agregado.calcular_totales()
    assert totales["total"] == 10.0


def test_cantidad_a_cero_en_linea_es_rechazada():
    agregado = _agregado_con_linea()
    with pytest.raises(ValidationException):
        agregado.modificar_cantidad("p1", 0)


def test_descuento_venta_sobre_linea_al_100_por_ciento_no_deberia_crashear():
    agregado = _agregado_con_linea(precio="10.00")
    agregado.aplicar_descuento_linea("p1", Decimal("100"))
    agregado.aplicar_descuento_venta(Decimal("50"))
    totales = agregado.calcular_totales()
    assert totales["total"] == 0.0


@pytest.mark.parametrize("linea,total", [("0", 5.0), ("25", 2.5), ("50", 0.0), ("75", 0.0), ("100", 0.0)])
def test_descuentos_combinados_no_superan_el_subtotal(linea, total):
    agregado = _agregado_con_linea(precio="10.00")
    agregado.aplicar_descuento_linea("p1", Decimal(linea))
    agregado.aplicar_descuento_venta(Decimal("50"))
    totales = agregado.calcular_totales()
    assert totales["total"] == total
    assert totales["descuento"] == 10.0 - total
    assert totales["subtotal"] == totales["descuento"] + totales["total"]
