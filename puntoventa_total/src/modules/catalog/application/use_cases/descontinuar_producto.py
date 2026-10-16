from src.modules.catalog.application.dto.producto_output import ProductoOutputDTO
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoNoEncontrado
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository


class DescontinuarProducto:
    def __init__(self, repo: ProductoRepository):
        self._repo = repo

    def ejecutar(self, producto_id: str, motivo: str = "") -> ProductoOutputDTO:
        producto = self._repo.buscar_por_id(producto_id)
        if producto is None:
            raise ProductoNoEncontrado(producto_id)
        producto.descontinuar(motivo)
        self._repo.guardar(producto)
        return ProductoOutputDTO.desde_entidad(producto)

