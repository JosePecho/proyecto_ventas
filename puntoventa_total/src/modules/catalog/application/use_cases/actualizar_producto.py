from __future__ import annotations

from src.modules.catalog.application.dto.producto_input import ActualizarProductoDTO
from src.modules.catalog.application.dto.producto_output import ProductoOutputDTO
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoNoEncontrado
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.shared.domain.value_objects.monto import Monto


class ActualizarProducto:
    def __init__(self, repo: ProductoRepository, moneda: str = "PEN"):
        self._repo = repo
        self._moneda = moneda

    def ejecutar(self, datos: ActualizarProductoDTO) -> ProductoOutputDTO:
        producto = self._repo.buscar_por_id(datos.producto_id)
        if producto is None:
            raise ProductoNoEncontrado(datos.producto_id)

        if datos.nombre:
            producto.renombrar(datos.nombre)
        if datos.descripcion is not None:
            producto.descripcion = datos.descripcion
        if datos.costo is not None or datos.precio_venta is not None:
            costo = Monto(datos.costo if datos.costo is not None else producto.precio.costo.valor, self._moneda)
            venta = Monto(
                datos.precio_venta if datos.precio_venta is not None else producto.precio.venta.valor,
                self._moneda,
            )
            producto.actualizar_precios(costo, venta)
        if datos.categoria_id is not None:
            producto.categoria_id = datos.categoria_id

        self._repo.guardar(producto)
        return ProductoOutputDTO.desde_entidad(producto)

