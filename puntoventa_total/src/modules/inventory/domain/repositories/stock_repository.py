from abc import ABC, abstractmethod
from typing import Optional

from src.modules.inventory.domain.entities.existencia import Existencia


class StockRepository(ABC):
    def disponibles(self, producto_ids) -> dict[str, int]:
        return {str(pid): self.disponible(str(pid)) for pid in producto_ids}

    def listar_existencias(self) -> list[dict]:
        raise NotImplementedError

    def umbral_minimo(self, producto_id: str, defecto: int = 5) -> int:
        return defecto

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
    def productos_bajo_minimo(self, umbral: int | None = None) -> list[dict]:
        ...

