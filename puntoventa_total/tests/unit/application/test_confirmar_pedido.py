from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.orders.application.use_cases.confirmar_pedido import ConfirmarPedido
from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _pedido() -> PedidoAggregate:
    agregado = PedidoAggregate(pedido=Pedido(numero="P1", cliente_nombre="Ana"))
    agregado.agregar_producto("p1", "Pizza", 1, Monto(Decimal("40.00")))
    return agregado


def test_confirmar_reserva_stock_y_cambia_estado():
    repo, inventario = MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = _pedido()
    inventario.reservar.return_value = "reserva-1"

    # el repositorio fake debe devolver el agregado al guardar
    repo.guardar.side_effect = lambda agregado: agregado

    resultado = ConfirmarPedido(repo, inventario).ejecutar("p1-id")

    assert resultado.estado == EstadoPedido.CONFIRMADO.value
    inventario.reservar.assert_called_once()


def test_pedido_vacio_no_se_confirma():
    from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException

    repo, inventario = MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = PedidoAggregate(pedido=Pedido(numero="P2", cliente_nombre="Ana"))

    with pytest.raises(PedidoException):
        ConfirmarPedido(repo, inventario).ejecutar("p2-id")

