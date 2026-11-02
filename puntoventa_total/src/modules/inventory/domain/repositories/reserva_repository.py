from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.inventory.domain.entities.reserva_stock import ReservaStock


class ReservaRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, reserva_id) -> ReservaStock | None:
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

