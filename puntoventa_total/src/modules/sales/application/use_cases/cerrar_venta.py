from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.domain.repositories.venta_repository import VentaRepository


class CerrarVenta:
    """Confirmacion explicita de cierre para flujo asistido por cajero."""

    def __init__(self, repo: VentaRepository):
        self._repo = repo

    def ejecutar(self, venta_id: str, usuario_id: str = "") -> VentaOutputDTO:
        agregado = self._repo.buscar_por_id(venta_id)
        if agregado is None:
            from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

            raise VentaNoEncontrada(venta_id)
        agregado.cerrar(usuario_id)
        self._repo.guardar(agregado)
        return VentaOutputDTO.desde_agregado(agregado)

