"""Caso de uso de cobro con inventario y auditoria fakes."""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _venta_total_10() -> VentaAggregate:
    agregado = VentaAggregate(venta=Venta(numero_ticket="T9", cajero_id="c1"))
    agregado.agregar_producto("p1", "Item", 1, Monto(Decimal("10.00")))
    agregado.calcular_totales()
    return agregado


def test_pago_efectivo_completo_cierra_venta():
    repo, inventario, auditoria = MagicMock(), MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = _venta_total_10()

    resultado = ProcesarPago(repo, inventario, auditoria).ejecutar(
        ProcesarPagoDTO(venta_id="v1", metodo="EFECTIVO", monto=10.0, monto_entregado=20.0)
    )

    assert resultado["estado"] == "PAGADA"
    assert resultado["vuelto"] == 10.0
    inventario.descontar.assert_called_once()
    auditoria.registrar.assert_called_once()


def test_pago_parcial_no_cierra():
    repo, inventario, auditoria = MagicMock(), MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = _venta_total_10()

    resultado = ProcesarPago(repo, inventario, auditoria).ejecutar(
        ProcesarPagoDTO(venta_id="v1", metodo="EFECTIVO", monto=4.0)
    )

    assert resultado["estado"] == "PENDIENTE"
    assert resultado["saldo"] == pytest.approx(6.0)
    inventario.descontar.assert_not_called()

