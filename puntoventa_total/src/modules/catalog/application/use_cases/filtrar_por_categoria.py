from __future__ import annotations

from src.modules.catalog.application.dto.producto_output import ProductoOutputDTO
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.shared.application.dto.pagination_dto import PageDTO


class FiltrarPorCategoria:
    def __init__(self, repo: ProductoRepository):
        self._repo = repo

    def ejecutar(self, categoria_id: str, pagina: int = 1, por_pagina: int = 20) -> PageDTO[ProductoOutputDTO]:
        pagina = max(pagina, 1)
        total = self._repo.contar(categoria_id=categoria_id)
        productos = self._repo.listar(categoria_id=categoria_id, limit=por_pagina)
        inicio = (pagina - 1) * por_pagina
        items = [ProductoOutputDTO.desde_entidad(p) for p in list(productos)[inicio : inicio + por_pagina]]
        return PageDTO(items=items, total=total, pagina=pagina, por_pagina=por_pagina)

