"""Puerto al modulo de ventas para consolidar el arqueo."""
from abc import ABC, abstractmethod
from typing import Sequence


class VentasTurnoPort(ABC):
    @abstractmethod
    def total_ventas(self, turno_id: str) -> float:
        ...

    @abstractmethod
    def pagos_del_turno(self, turno_id: str) -> Sequence[dict]:
        """Devuelve [{"metodo": str, "monto": float}, ...]."""
        ...

    @abstractmethod
    def contar_ventas(self, turno_id: str) -> int:
        ...

