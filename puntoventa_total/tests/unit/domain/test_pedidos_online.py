from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.modules.orders.application.use_cases.confirmar_pedido import ConfirmarPedido
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("estado", list(EstadoPedido))
def test_cancelacion_solo_borrador_o_pendiente(estado):
    pedido = PedidoAggregate(Pedido(cliente_nombre="Ana", estado=estado))
    if estado in (EstadoPedido.BORRADOR, EstadoPedido.CONFIRMADO):
        pedido.cancelar()
        assert pedido.pedido.estado == EstadoPedido.CANCELADO
    else:
        with pytest.raises(PedidoException):
            pedido.cancelar()
        assert pedido.pedido.estado == estado


@pytest.mark.parametrize("cantidad", [0, -1, True, 1.5])
def test_cantidad_invalida_no_modifica_linea_existente(cantidad):
    pedido = PedidoAggregate(Pedido(cliente_nombre="Ana"))
    pedido.agregar_producto("p1", "Pan", 3, Monto(Decimal("2")))
    with pytest.raises(PedidoException):
        pedido.agregar_producto("p1", "Pan", cantidad, Monto(Decimal("2")))
    assert pedido.lineas[0].cantidad == 3


@pytest.mark.parametrize("segundos", [1, 59])
def test_franja_rechaza_segundos(segundos):
    hora = (datetime.now(timezone.utc) + timedelta(days=1)).replace(minute=30, second=segundos, microsecond=0)
    with pytest.raises(PedidoException):
        Pedido(cliente_nombre="Ana").asignar_hora_recojo(hora)


def test_reconfirmacion_no_reserva_stock_otra_vez():
    pedido = PedidoAggregate(Pedido(cliente_nombre="Ana"))
    pedido.agregar_producto("p1", "Pan", 2, Monto(Decimal("2")))
    pedido.confirmar()
    repo, inventario = Mock(), Mock()
    repo.buscar_por_id.return_value = pedido
    with pytest.raises(PedidoException):
        ConfirmarPedido(repo, inventario).ejecutar(str(pedido.pedido.id))
    inventario.reservar.assert_not_called()


def test_pedido_confirmado_no_admite_cambios():
    pedido = PedidoAggregate(Pedido(cliente_nombre="Ana"))
    pedido.agregar_producto("p1", "Pan", 2, Monto(Decimal("2")))
    pedido.confirmar()
    with pytest.raises(PedidoException):
        pedido.agregar_producto("p1", "Pan", 1, Monto(Decimal("2")))


def test_beat_conserva_recuperacion_de_emails_pendientes():
    from config.celery import app
    assert app.conf.beat_schedule["pedidos-listos-pendientes"]["task"] == "src.modules.orders.tasks.reintentar_notificaciones"
    assert "verificar-stock-minimo-diario" in app.conf.beat_schedule
