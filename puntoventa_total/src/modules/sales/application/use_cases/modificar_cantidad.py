from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.domain.repositories.venta_repository import VentaRepository


class ModificarCantidad:
    def __init__(self, repo: VentaRepository):
        self._repo = repo

    def ejecutar(self, venta_id: str, producto_id: str, cantidad: int) -> VentaOutputDTO:
        agregado = self._repo.buscar_por_id(venta_id)
        if agregado is None:
            from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

            raise VentaNoEncontrada(venta_id)
        agregado.modificar_cantidad(producto_id, cantidad)
        agregado.calcular_totales()
        self._repo.guardar(agregado)
        return VentaOutputDTO.desde_agregado(agregado)

