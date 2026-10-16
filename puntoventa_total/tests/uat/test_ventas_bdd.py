"""Nivel 4 - UAT/BDD: automatizacion de los escenarios Gherkin del POS.

Los step definitions ejercitan los casos de uso y el agregado REALES del
modulo sales; solo los puertos externos (inventario, auditoria) se sustituyen
por dobles. Aprobacion formal del Product Owner: ver
docs/testing/test_master_plan.md, seccion 7.3.
"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from src.modules.sales.application.use_cases.anular_venta import AnularVenta
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.pago import Pago
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.exceptions.venta_exceptions import (
    PagoInsuficiente,
    VentaException,
)
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.uat

scenarios("features/ventas_pos.feature")


# --- fixtures compartidas --------------------------------------------------


@pytest.fixture
def contexto():
    """Memoria del escenario: ultimo error capturado y dobles de inventario."""
    return {"error": None, "inventario": None, "devoluciones": 0}


def _venta(cantidad: int, producto: str, precio: str) -> VentaAggregate:
    agregado = VentaAggregate(venta=Venta(numero_ticket="TUAT", cajero_id="cajero-1"))
    agregado.agregar_producto("p1", producto, cantidad, Monto(Decimal(precio)))
    agregado.calcular_totales()
    return agregado


# --- Given -----------------------------------------------------------------


@given(
    parsers.parse('una venta en borrador con {cantidad:d} "{producto}" a "{precio}"'),
    target_fixture="venta",
)
def venta_en_borrador(cantidad: int, producto: str, precio: str) -> VentaAggregate:
    return _venta(cantidad, producto, precio)


@given(
    parsers.parse('una venta pagada con {cantidad:d} "{producto}" a "{precio}"'),
    target_fixture="venta",
)
def venta_pagada(cantidad: int, producto: str, precio: str) -> VentaAggregate:
    agregado = _venta(cantidad, producto, precio)
    total = Decimal(str(agregado.venta.total))
    agregado.registrar_pago(Pago.efectivo("TUAT", Monto(total)))
    agregado.cerrar()
    return agregado


@given(parsers.parse('la caja registra un pago de "{monto}" con "{entregado}" entregados en efectivo'))
def caja_registra_pago(venta: VentaAggregate, monto: str, entregado: str) -> None:
    venta.registrar_pago(
        Pago.efectivo("TUAT", Monto(Decimal(monto)), Monto(Decimal(entregado)))
    )


# --- When ------------------------------------------------------------------


@when("el cajero cierra la venta")
def cajero_cierra(venta: VentaAggregate) -> None:
    venta.cerrar()


@when("el cajero intenta cerrar la venta")
def cajero_intenta_cerrar(venta: VentaAggregate, contexto: dict) -> None:
    try:
        venta.cerrar()
    except PagoInsuficiente as exc:
        contexto["error"] = exc


@when(parsers.parse('el gerente aplica un descuento del "{pct:d}" por ciento a la venta'))
def gerente_aplica_descuento(venta: VentaAggregate, pct: int, contexto: dict) -> None:
    try:
        venta.aplicar_descuento_venta(Decimal(pct))
        venta.calcular_totales()
    except VentaException as exc:
        contexto["error"] = exc


@when(parsers.parse('el gerente anula la venta con motivo "{motivo}"'))
def gerente_anula(venta: VentaAggregate, motivo: str, contexto: dict) -> None:
    repo, inventario, auditoria = MagicMock(), MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = venta
    contexto["inventario"] = inventario
    try:
        AnularVenta(repo, inventario, auditoria).ejecutar("v1", motivo, "gerente-1")
    except VentaException as exc:
        contexto["error"] = exc
    else:
        if inventario.devolver.call_count:
            contexto["devoluciones"] += 1


# --- Then ------------------------------------------------------------------


@then(parsers.parse('la venta queda "{estado}"'))
def venta_queda(venta: VentaAggregate, estado: str) -> None:
    assert venta.venta.estado.value == estado


@then(parsers.parse('la venta sigue en estado "{estado}"'))
def venta_sigue_en(venta: VentaAggregate, estado: str) -> None:
    assert venta.venta.estado.value == estado


@then(parsers.parse('el vuelto del cajero es "{vuelto}"'))
def vuelto_es(venta: VentaAggregate, vuelto: str) -> None:
    ultimo_pago = venta.pagos[-1]
    assert ultimo_pago.vuelto is not None
    assert ultimo_pago.vuelto.valor == Decimal(vuelto)


@then("el cierre se rechaza por saldo pendiente")
def cierre_rechazado(contexto: dict) -> None:
    assert isinstance(contexto["error"], PagoInsuficiente)
    assert contexto["error"].faltante == 6.0


@then("el descuento se rechaza con el tope de 50 por ciento")
def descuento_rechazado(contexto: dict) -> None:
    assert isinstance(contexto["error"], VentaException)
    assert "50%" in str(contexto["error"])


@then(parsers.parse('el total de la venta queda en "{total}"'))
def total_es(venta: VentaAggregate, total: str) -> None:
    assert Decimal(str(venta.venta.total)) == Decimal(total)


@then("el inventario recibe una devolucion de stock")
def inventario_recibe_devolucion(contexto: dict) -> None:
    assert contexto["inventario"].devolver.call_count == 1


@then("la segunda anulacion se rechaza")
def segunda_anulacion_rechazada(contexto: dict) -> None:
    assert isinstance(contexto["error"], VentaException)
    assert contexto["error"].codigo == "VENTA_NO_MODIFICABLE"


@then("el inventario no recibe una segunda devolucion")
def sin_segunda_devolucion(contexto: dict) -> None:
    assert contexto["inventario"].devolver.call_count == 0
    assert contexto["devoluciones"] == 1
