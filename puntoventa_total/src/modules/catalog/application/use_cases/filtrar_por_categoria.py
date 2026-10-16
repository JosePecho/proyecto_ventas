from __future__ import annotations

from src.modules.catalog.application.dto.producto_output import ProductoOutputDTO
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.shared.application.dto.pagination_dto import PageDTO
from src.modules.catalog.application.use_cases.listar_productos import ListarProductos


class FiltrarPorCategoria:
    def __init__(self, repo: ProductoRepository):
        self._repo = repo

    def ejecutar(self, categoria_id: str, pagina: int = 1, por_pagina: int = 20) -> PageDTO[ProductoOutputDTO]:
        return ListarProductos(self._repo).ejecutar(pagina=pagina, por_pagina=por_pagina, categoria_id=categoria_id)

