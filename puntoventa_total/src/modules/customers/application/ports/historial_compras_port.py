"""Puerto al modulo de ventas para el historial del cliente."""
from abc import ABC, abstractmethod
from typing import Sequence


class HistorialComprasPort(ABC):
    @abstractmethod
    def compras_del_cliente(self, cliente_id: str) -> Sequence[dict]:
        """Devuelve [{"fecha": datetime, "total": float, "numero_ticket": str}, ...]."""
        ...

    @abstractmethod
    def total_gastado(self, cliente_id: str) -> float:
        ...

