from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.catalog.domain.entities.categoria import Categoria


class CategoriaRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, categoria_id) -> Categoria | None:
        ...

    @abstractmethod
    def buscar_por_slug(self, slug: str) -> Categoria | None:
        ...

    @abstractmethod
    def listar(self, solo_activas: bool = True) -> Sequence[Categoria]:
        ...

    @abstractmethod
    def guardar(self, categoria: Categoria) -> Categoria:
        ...

