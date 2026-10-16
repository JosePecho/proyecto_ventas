from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.modules.inventory.domain.entities.reserva_stock import ReservaStock


class ReservaRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, reserva_id) -> Optional[ReservaStock]:
        ...

    @abstractmethod
    def listar_por_referencia(self, referencia: str) -> Sequence[ReservaStock]:
        ...

    @abstractmethod
    def listar_activas_expiradas(self) -> Sequence[ReservaStock]:
        ...

    @abstractmethod
    def guardar(self, reserva: ReservaStock) -> ReservaStock:
        ...

