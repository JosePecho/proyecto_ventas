"""Invariantes de la venta: lineas, descuentos, cobro y anulacion."""
from decimal import Decimal

import pytest

from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.domain.exceptions.venta_exceptions import (
    ProductoYaAgregado,
    VentaException,
)
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _agregado() -> VentaAggregate:
    return VentaAggregate(venta=Venta(numero_ticket="T0001", cajero_id="cajero-1"))


def test_agregar_producto_calcula_totales():
    agregado = _agregado()
    agregado.agregar_producto("p1", "Gaseosa", 2, Monto(Decimal("4.50")))
    totales = agregado.calcular_totales()
    assert totales["subtotal"] == 9.0
    assert totales["total"] == 9.0


def test_no_se_puede_duplicar_producto():
    agregado = _agregado()
    agregado.agregar_producto("p1", "Gaseosa", 1, Monto(Decimal("4.50")))
    with pytest.raises(ProductoYaAgregado):
        agregado.agregar_producto("p1", "Gaseosa", 1, Monto(Decimal("4.50")))


def test_cerrar_sin_pago_total_lanza_error():
    agregado = _agregado()
    agregado.agregar_producto("p1", "Pan", 1, Monto(Decimal("1.00")))
    agregado.calcular_totales()  # sin esto venta.total=0 y cerrar() no valida nada
    from src.modules.sales.domain.entities.pago import Pago
    from src.modules.sales.domain.exceptions.venta_exceptions import PagoInsuficiente

    agregado.registrar_pago(Pago.efectivo("T0001", Monto(Decimal("0.50"))))
    with pytest.raises(PagoInsuficiente):
        agregado.cerrar()
    assert agregado.venta.estado == EstadoVenta.BORRADOR


def test_cierre_correcto_publica_evento():
    agregado = _agregado()
    agregado.agregar_producto("p1", "Pan", 3, Monto(Decimal("2.00")))
    from src.modules.sales.domain.entities.pago import Pago

    entregado = Monto(Decimal("10.00"))
    agregado.registrar_pago(Pago.efectivo("T0001", Monto(Decimal("6.00")), entregado))
    agregado.cerrar()

    assert agregado.venta.estado == EstadoVenta.PAGADA
    eventos = agregado.venta.eventos_pendientes()
    assert any(e.nombre == "VentaPagada" for e in eventos)


def test_anulacion_de_venta_pagada_queda_registrada():
    agregado = _agregado()
    agregado.venta.marcar_pagada()
    agregado.anular("cliente se equivoco", "gerente-1")
    assert agregado.venta.estado == EstadoVenta.ANULADA
    assert any(e.nombre == "VentaAnulada" for e in agregado.venta.eventos_pendientes())

