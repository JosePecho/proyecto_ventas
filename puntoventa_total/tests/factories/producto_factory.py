"""Factory-boy para productos del catalogo."""
import factory
from decimal import Decimal

from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.enums.estado_producto import EstadoProducto
from src.modules.catalog.domain.value_objects.precio import Precio
from src.shared.domain.value_objects.monto import Monto


class ProductoFactory(factory.Factory):
    class Meta:
        model = Producto

    nombre = factory.Sequence(lambda n: f"Producto {n}")
    descripcion = "Producto generado por factory"
    codigo_barras = factory.Sequence(lambda n: f"775{n:010d}")
    precio = factory.LazyAttribute(
        lambda o: Precio(costo=Monto(Decimal("5.00")), venta=Monto(Decimal("8.50")))
    )
    estado = EstadoProducto.ACTIVO
    activo = True


class ProductoAgotadoFactory(ProductoFactory):
    """Producto no vendible: inactivo/discontinuado (el stock se maneja en inventory)."""

    estado = EstadoProducto.INACTIVO
    activo = False

