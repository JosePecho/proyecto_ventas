from __future__ import annotations

from src.modules.catalog.application.dto.producto_input import ActualizarProductoDTO
from src.modules.catalog.application.dto.producto_output import ProductoOutputDTO
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoNoEncontrado, CodigoBarrasDuplicado
from src.shared.domain.value_objects.codigo_barras import CodigoBarras
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
        if datos.codigo_barras is not None:
            if self._repo.existe_codigo_barras(datos.codigo_barras, excluir_id=producto.id):
                raise CodigoBarrasDuplicado(datos.codigo_barras)
            producto.codigo_barras = CodigoBarras(datos.codigo_barras)
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
        if datos.stock_minimo is not None:
            if datos.stock_minimo < 0:
                raise ValueError("El stock minimo no puede ser negativo")
            producto.stock_minimo = datos.stock_minimo
        if datos.actualizar_vencimiento or datos.fecha_vencimiento is not None:
            producto.fecha_vencimiento = datos.fecha_vencimiento

        self._repo.guardar(producto)
        return ProductoOutputDTO.desde_entidad(producto)

