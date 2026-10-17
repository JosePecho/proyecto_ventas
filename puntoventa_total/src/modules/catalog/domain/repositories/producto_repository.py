from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.modules.catalog.domain.entities.producto import Producto


class ProductoRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, producto_id) -> Optional[Producto]:
        ...

    @abstractmethod
    def buscar_por_codigo_barras(self, codigo: str) -> Optional[Producto]:
        ...

    @abstractmethod
    def listar(
        self,
        incluir_inactivos: bool = False,
        termino: str | None = None,
        categoria_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[Producto]:
        ...

    @abstractmethod
    def contar(self, incluir_inactivos: bool = False, termino: str | None = None, categoria_id: str | None = None) -> int:
        ...

    @abstractmethod
    def guardar(self, producto: Producto) -> Producto:
        ...

    @abstractmethod
    def existe_codigo_barras(self, codigo: str, excluir_id=None) -> bool:
        ...

