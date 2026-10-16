from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.modules.catalog.domain.entities.categoria import Categoria


class CategoriaRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, categoria_id) -> Optional[Categoria]:
        ...

    @abstractmethod
    def buscar_por_slug(self, slug: str) -> Optional[Categoria]:
        ...

    @abstractmethod
    def listar(self, solo_activas: bool = True) -> Sequence[Categoria]:
        ...

    @abstractmethod
    def guardar(self, categoria: Categoria) -> Categoria:
        ...

