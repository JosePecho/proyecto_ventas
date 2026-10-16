from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.modules.cash_register.domain.entities.movimiento_caja import MovimientoCaja
from src.modules.cash_register.domain.entities.turno_caja import TurnoCaja


class TurnoRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, turno_id) -> Optional[TurnoCaja]:
        ...

    @abstractmethod
    def buscar_abierto_por_cajero(self, cajero_id: str) -> Optional[TurnoCaja]:
        ...

    @abstractmethod
    def guardar(self, turno: TurnoCaja) -> TurnoCaja:
        ...

    @abstractmethod
    def registrar_movimiento(self, movimiento: MovimientoCaja) -> MovimientoCaja:
        ...

    @abstractmethod
    def movimientos_del_turno(self, turno_id: str) -> Sequence[MovimientoCaja]:
        ...

    @abstractmethod
    def listar_historico(self, limite: int = 30) -> Sequence[TurnoCaja]:
        ...

