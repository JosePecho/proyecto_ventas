from abc import ABC, abstractmethod
from typing import Sequence

from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock


class MovimientoRepository(ABC):
    def contar_kardex(self, producto_id: str, desde=None, hasta=None) -> int:
        return len(self.kardex(producto_id, desde, hasta, limite=None))

    @abstractmethod
    def guardar(self, movimiento: MovimientoStock) -> MovimientoStock:
        ...

    @abstractmethod
    def kardex(self, producto_id: str, desde=None, hasta=None, limite: int | None = 200) -> Sequence[MovimientoStock]:
        ...

    @abstractmethod
    def total_entradas(self, producto_id: str) -> int:
        ...

