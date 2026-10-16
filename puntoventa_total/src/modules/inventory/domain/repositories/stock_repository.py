from abc import ABC, abstractmethod
from typing import Optional

from src.modules.inventory.domain.entities.existencia import Existencia


class StockRepository(ABC):
    @abstractmethod
    def obtener(self, producto_id: str) -> Optional[Existencia]:
        ...

    @abstractmethod
    def disponible(self, producto_id: str) -> int:
        ...

    @abstractmethod
    def guardar(self, existencia: Existencia) -> Existencia:
        ...

    @abstractmethod
    def productos_bajo_minimo(self, umbral: int) -> list[dict]:
        ...

