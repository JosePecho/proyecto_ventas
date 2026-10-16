from __future__ import annotations

from typing import Optional

from src.modules.inventory.application.dto.movimiento_dto import MovimientoDTO
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.shared.application.dto.pagination_dto import PageDTO


class ConsultarKardex:
    def __init__(self, repo: MovimientoRepository):
        self._repo = repo

    def ejecutar(
        self,
        producto_id: str,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
        pagina: int = 1,
        por_pagina: int = 50,
    ) -> PageDTO[MovimientoDTO]:
        import datetime as dt

        desde_dt = dt.date.fromisoformat(desde) if desde else None
        hasta_dt = dt.date.fromisoformat(hasta) if hasta else None
        movimientos = self._repo.kardex(producto_id, desde_dt, hasta_dt, limite=por_pagina * pagina)
        inicio = (pagina - 1) * por_pagina
        fragmento = list(movimientos)[inicio : inicio + por_pagina]
        return PageDTO(
            items=[MovimientoDTO.desde_entidad(m) for m in fragmento],
            total=len(list(movimientos)),
            pagina=pagina,
            por_pagina=por_pagina,
        )

