"""Puerto al modulo de inventario: el catalogo nunca importa inventory."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class DisponibilidadPort(ABC):
    @abstractmethod
    def stock_disponible(self, producto_id: str) -> int:
        ...

    @abstractmethod
    def stock_disponible_lote(self, producto_ids: Iterable[str]) -> dict[str, int]:
        """Devuelve {producto_id: stock_disponible}."""
        ...

    @abstractmethod
    def tiene_stock_minimo(self, producto_id: str) -> bool:
        ...

