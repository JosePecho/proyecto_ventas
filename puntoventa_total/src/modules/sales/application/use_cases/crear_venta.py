from __future__ import annotations

from src.modules.sales.application.dto.venta_input import CrearVentaDTO
from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.repositories.venta_repository import VentaRepository


class CrearVenta:
    def __init__(self, repo: VentaRepository):
        self._repo = repo

    def ejecutar(self, datos: CrearVentaDTO) -> VentaOutputDTO:
        venta = Venta(
            numero_ticket=self._repo.siguiente_numero_ticket(),
            cajero_id=datos.cajero_id,
            turno_caja_id=datos.turno_caja_id,
            cliente_id=datos.cliente_id,
            moneda=datos.moneda,
        )
        agregado = VentaAggregate(venta=venta)
        self._repo.guardar(agregado)
        return VentaOutputDTO.desde_agregado(agregado)

