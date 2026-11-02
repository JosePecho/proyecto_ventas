from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.inventory.domain.entities.lote import Lote


class LoteRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, lote_id) -> Lote | None:
        ...

    @abstractmethod
    def listar_por_producto(self, producto_id: str, solo_pendientes: bool = True) -> Sequence[Lote]:
        """Lotes ordenados por vencimiento (PEPS)."""
        ...

    @abstractmethod
    def guardar(self, lote: Lote) -> Lote:
        ...

    @abstractmethod
    def lotes_por_vencer(self, dias: int) -> Sequence[Lote]:
        ...

    @abstractmethod
    def lotes_vencidos(self) -> Sequence[Lote]:
        ...

