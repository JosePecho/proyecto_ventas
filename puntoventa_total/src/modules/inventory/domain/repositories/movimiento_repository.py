from abc import ABC, abstractmethod
from typing import Sequence

from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock


class MovimientoRepository(ABC):
    @abstractmethod
    def guardar(self, movimiento: MovimientoStock) -> MovimientoStock:
        ...

    @abstractmethod
    def kardex(self, producto_id: str, desde=None, hasta=None, limite: int = 200) -> Sequence[MovimientoStock]:
        ...

    @abstractmethod
    def total_entradas(self, producto_id: str) -> int:
        ...

