from datetime import date

from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.shared.application.dto.pagination_dto import PageDTO


class ConsultarVenta:
    def __init__(self, repo: VentaRepository):
        self._repo = repo

    def por_ticket(self, numero_ticket: str) -> VentaOutputDTO:
        agregado = self._repo.buscar_por_numero_ticket(numero_ticket)
        if agregado is None:
            from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

            raise VentaNoEncontrada(numero_ticket)
        return VentaOutputDTO.desde_agregado(agregado)

    def del_dia(self, dia: date | None = None, pagina: int = 1, por_pagina: int = 25) -> PageDTO:
        dia = dia or date.today()
        ventas = self._repo.listar_por_fecha(dia, dia)
        inicio = (pagina - 1) * por_pagina
        fragmento = list(ventas)[inicio : inicio + por_pagina]
        return PageDTO(
            items=[VentaOutputDTO.desde_agregado(v) for v in fragmento],
            total=len(list(ventas)),
            pagina=pagina,
            por_pagina=por_pagina,
        )

    def del_turno(self, turno_caja_id: str) -> list[VentaOutputDTO]:
        return [VentaOutputDTO.desde_agregado(v) for v in self._repo.listar_por_turno(turno_caja_id)]

