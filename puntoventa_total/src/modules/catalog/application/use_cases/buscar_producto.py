"""Busqueda por texto libre sobre nombre/descripcion."""
from __future__ import annotations

from typing import Sequence

from src.modules.catalog.application.dto.producto_output import ProductoOutputDTO
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.shared.infrastructure.cache.redis_cache import cache_resultado


class BuscarProducto:
    def __init__(self, repo: ProductoRepository):
        self._repo = repo

    @cache_resultado(segundos=120, prefijo="catalogo:buscar")
    def ejecutar(self, termino: str, limite: int = 50) -> list[ProductoOutputDTO]:
        productos = self._repo.listar(termino=termino.strip(), limit=limite)
        return [ProductoOutputDTO.desde_entidad(p) for p in productos]

