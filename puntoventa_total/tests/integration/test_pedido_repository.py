import uuid

import pytest

from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.infrastructure.factories import construir_pedido_repository

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_pedido_guarda_numero_unico():
    repo = construir_pedido_repository()
    agregado = PedidoAggregate(pedido=Pedido(numero="PINT1", cliente_nombre="Luis"))
    repo.guardar(agregado)

    assert repo.buscar_por_numero("PINT1") is not None


def test_listar_por_cliente_filtra():
    # el mapper exige cliente_id con formato UUID (PedidoMapper.guardar_agregado)
    cliente_luis = str(uuid.uuid4())
    cliente_rosa = str(uuid.uuid4())
    repo = construir_pedido_repository()
    repo.guardar(PedidoAggregate(pedido=Pedido(numero="PINT2", cliente_nombre="Luis", cliente_id=cliente_luis)))
    repo.guardar(PedidoAggregate(pedido=Pedido(numero="PINT3", cliente_nombre="Rosa", cliente_id=cliente_rosa)))

    pedidos = repo.listar_por_cliente(cliente_luis)
    assert len(pedidos) == 1
    assert pedidos[0].pedido.cliente_nombre == "Luis"

