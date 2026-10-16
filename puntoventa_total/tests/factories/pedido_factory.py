import factory

from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido


class PedidoFactory(factory.Factory):
    class Meta:
        model = Pedido

    numero = factory.Sequence(lambda n: f"PTEST{n:04d}")
    cliente_nombre = factory.Sequence(lambda n: f"Comprador {n}")
    cliente_telefono = "999111222"


class PedidoAggregateFactory(factory.Factory):
    class Meta:
        model = PedidoAggregate

    pedido = factory.SubFactory(PedidoFactory)
    lineas = factory.LazyFunction(list)

