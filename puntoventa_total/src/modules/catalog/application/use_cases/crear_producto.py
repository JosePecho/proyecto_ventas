from __future__ import annotations

from decimal import Decimal

from src.modules.catalog.application.dto.producto_input import ProductoInputDTO
from src.modules.catalog.application.dto.producto_output import ProductoOutputDTO
from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.exceptions.producto_exceptions import CodigoBarrasDuplicado
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.modules.catalog.domain.value_objects.precio import Precio
from src.shared.domain.value_objects.monto import Monto


class CrearProducto:
    def __init__(self, repo: ProductoRepository, moneda: str = "PEN"):
        self._repo = repo
        self._moneda = moneda

    def ejecutar(self, datos: ProductoInputDTO) -> ProductoOutputDTO:
        if self._repo.existe_codigo_barras(datos.codigo_barras):
            raise CodigoBarrasDuplicado(datos.codigo_barras)

        producto = Producto(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            codigo_barras=datos.codigo_barras,
            precio=Precio(
                costo=Monto(datos.costo, self._moneda),
                venta=Monto(datos.precio_venta, self._moneda),
            ),
            categoria_id=datos.categoria_id,
            imagen=datos.imagen,
            unidad_medida=datos.unidad_medida,
            requiere_stock=datos.requiere_stock,
        )
        self._repo.guardar(producto)
        return ProductoOutputDTO.desde_entidad(producto)

