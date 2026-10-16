from decimal import Decimal

import pytest

from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.modules.orders.domain.exceptions.pedido_exceptions import TransicionInvalida
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _pedido() -> PedidoAggregate:
    return PedidoAggregate(pedido=Pedido(numero="P0001", cliente_nombre="Maria"))


def test_pedido_calcula_total_con_lineas():
    pedido = _pedido()
    pedido.agregar_producto("p1", "Torta", 2, Monto(Decimal("30.00")))
    assert pedido.pedido.total == 60.0


def test_flujo_de_estados_es_valido():
    pedido = _pedido()
    pedido.agregar_producto("p1", "Torta", 1, Monto(Decimal("30.00")))
    pedido.confirmar()
    pedido.iniciar_preparacion()
    pedido.marcar_listo()
    pedido.entregar()
    assert pedido.pedido.estado == EstadoPedido.ENTREGADO


def test_transicion_invalida_se_rechaza():
    pedido = _pedido()
    with pytest.raises(TransicionInvalida):
        pedido.entregar()


def test_hora_de_recojo_en_pasado_se_rechaza():
    from datetime import datetime, timedelta

    from src.modules.orders.domain.exceptions.pedido_exceptions import HoraRecojoInvalida

    pedido = _pedido()
    with pytest.raises(HoraRecojoInvalida):
        pedido.pedido.asignar_hora_recojo(datetime.now() - timedelta(hours=1))


def test_cancelar_libera_el_pedido():
    pedido = _pedido()
    pedido.agregar_producto("p1", "Jugo", 1, Monto(Decimal("8.00")))
    pedido.cancelar("cambio de opinion")
    assert pedido.pedido.estado == EstadoPedido.CANCELADO

