"""Nivel 1 - aplicacion: caso de uso AnularVenta con inventario/auditoria fakes.

RN-06: la anulacion es unica y, si la venta estaba PAGADA, cada linea debe
devolverse al inventario (entrada compensatoria) una sola vez.
"""
from decimal import Decimal
from unittest.mock import MagicMock, call

import pytest

from src.modules.sales.application.use_cases.anular_venta import AnularVenta
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.pago import Pago
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.domain.exceptions.venta_exceptions import (
    VentaNoEncontrada,
    VentaNoModificable,
)
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _venta_con_lineas(estado: EstadoVenta, cantidad_lineas: int = 1) -> VentaAggregate:
    agregado = VentaAggregate(venta=Venta(numero_ticket="T100", cajero_id="cajero-1"))
    for i in range(cantidad_lineas):
        agregado.agregar_producto(f"p{i}", f"Producto {i}", 2, Monto(Decimal("5.00")))
    agregado.calcular_totales()
    if estado == EstadoVenta.PAGADA:
        agregado.registrar_pago(Pago.efectivo("T100", Monto(Decimal(str(10.0 * cantidad_lineas)))))
        agregado.cerrar()
    elif estado == EstadoVenta.ANULADA:
        agregado.anular("previa", "gerente-1")
    return agregado


def _sut(agregado):
    repo, inventario, auditoria = MagicMock(), MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = agregado
    return AnularVenta(repo, inventario, auditoria), repo, inventario, auditoria


def test_anular_venta_pagada_devuelve_stock_por_cada_linea():
    sut, repo, inventario, auditoria = _sut(_venta_con_lineas(EstadoVenta.PAGADA, cantidad_lineas=2))

    resultado = sut.ejecutar("v1", "cliente se equivoco", "gerente-1")

    assert resultado["estado"] == "ANULADA"
    assert inventario.devolver.call_count == 2
    assert inventario.devolver.call_args_list == [
        call("p0", 2, "ANULACION:T100", "gerente-1"),
        call("p1", 2, "ANULACION:T100", "gerente-1"),
    ]
    repo.guardar.assert_called_once()
    auditoria.registrar.assert_called_once()
    assert auditoria.registrar.call_args.kwargs["accion"] == "VENTA_ANULADA"


def test_anular_venta_en_borrador_no_toca_inventario():
    sut, repo, inventario, auditoria = _sut(_venta_con_lineas(EstadoVenta.BORRADOR))

    resultado = sut.ejecutar("v1", "cliente compro otra cosa", "cajero-1")

    assert resultado["estado"] == "ANULADA"
    inventario.devolver.assert_not_called()
    repo.guardar.assert_called_once()
    auditoria.registrar.assert_called_once()


def test_anular_venta_inexistente_lanza_excepcion_de_dominio():
    sut, repo, inventario, _ = _sut(None)
    with pytest.raises(VentaNoEncontrada):
        sut.ejecutar("fantasma", "motivo", "gerente-1")
    repo.guardar.assert_not_called()
    inventario.devolver.assert_not_called()


def test_anular_dos_veces_es_rechazado_y_no_devuelve_stock():
    agregado = _venta_con_lineas(EstadoVenta.PAGADA)
    sut, repo, inventario, _ = _sut(agregado)
    sut.ejecutar("v1", "motivo valido", "gerente-1")

    inventario.devolver.reset_mock()
    with pytest.raises(VentaNoModificable):
        sut.ejecutar("v1", "segundo intento", "gerente-1")

    inventario.devolver.assert_not_called()
    assert agregado.venta.estado == EstadoVenta.ANULADA
