"""Factory-boy para agregados de venta."""
import uuid
from decimal import Decimal

import factory

from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.shared.domain.value_objects.monto import Monto


class VentaFactory(factory.Factory):
    class Meta:
        model = Venta

    numero_ticket = factory.Sequence(lambda n: f"TTEST{n:05d}")
    cajero_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    estado = EstadoVenta.BORRADOR
    moneda = "PEN"


class VentaAggregateFactory(factory.Factory):
    class Meta:
        model = VentaAggregate

    venta = factory.SubFactory(VentaFactory)
    lineas = factory.LazyFunction(list)
    pagos = factory.LazyFunction(list)


def venta_con_linea(producto_id: str, nombre: str, cantidad: int = 1, precio: str = "8.50") -> VentaAggregate:
    agregado = VentaAggregateFactory()
    agregado.agregar_producto(producto_id, nombre, cantidad, Monto(Decimal(precio)))
    return agregado

