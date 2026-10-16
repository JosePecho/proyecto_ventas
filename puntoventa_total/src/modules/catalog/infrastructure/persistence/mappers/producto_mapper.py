import uuid
from decimal import Decimal

from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.enums.estado_producto import EstadoProducto
from src.modules.catalog.domain.value_objects.precio import Precio
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
from src.shared.domain.value_objects.codigo_barras import CodigoBarras
from src.shared.domain.value_objects.monto import Monto


class ProductoMapper:
    @staticmethod
    def a_dominio(m: ProductoModel) -> Producto:
        return Producto(
            id=m.id,
            nombre=m.nombre,
            descripcion=m.descripcion,
            codigo_barras=CodigoBarras(m.codigo_barras),
            precio=Precio(costo=Monto(Decimal(m.costo)), venta=Monto(Decimal(m.precio_venta))),
            categoria_id=str(m.categoria_id) if m.categoria_id else None,
            estado=EstadoProducto(m.estado),
            imagen=m.imagen.name if m.imagen else "",
            unidad_medida=m.unidad_medida,
            requiere_stock=m.requiere_stock,
            stock_minimo=m.stock_minimo,
            fecha_vencimiento=m.fecha_vencimiento,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    @staticmethod
    def a_modelo(e: Producto, m: ProductoModel | None = None) -> ProductoModel:
        m = m or ProductoModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.nombre = e.nombre
        m.descripcion = e.descripcion
        m.codigo_barras = str(e.codigo_barras)
        m.costo = e.precio.costo.valor
        m.precio_venta = e.precio.venta.valor
        m.estado = e.estado.value
        m.unidad_medida = e.unidad_medida
        m.requiere_stock = e.requiere_stock
        m.stock_minimo = e.stock_minimo
        m.fecha_vencimiento = e.fecha_vencimiento
        m.categoria_id = e.categoria_id
        m.activo = e.activo
        if e.imagen and not m.imagen:
            m.imagen = e.imagen
        return m

