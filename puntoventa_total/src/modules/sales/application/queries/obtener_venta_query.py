from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.shared.application.exceptions.application_exception import NotFoundException


class ObtenerVentaQuery:
    def __init__(self, repo: VentaRepository):
        self._repo = repo

    def por_id(self, venta_id: str) -> VentaOutputDTO:
        agregado = self._repo.buscar_por_id(venta_id)
        if agregado is None:
            raise NotFoundException(f"Venta {venta_id} no existe")
        return VentaOutputDTO.desde_agregado(agregado)

    def por_ticket(self, numero_ticket: str) -> VentaOutputDTO:
        agregado = self._repo.buscar_por_numero_ticket(numero_ticket)
        if agregado is None:
            raise NotFoundException(f"Ticket {numero_ticket} no existe")
        return VentaOutputDTO.desde_agregado(agregado)

