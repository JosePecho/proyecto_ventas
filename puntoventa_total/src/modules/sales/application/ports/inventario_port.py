from abc import ABC, abstractmethod
from typing import Iterable


class InventarioPort(ABC):
    """Puerto hacia el modulo inventory (el POS no conoce su implementacion)."""

    @abstractmethod
    def descontar(self, producto_id: str, cantidad: int, referencia: str, usuario_id: str = "") -> int:
        ...

    @abstractmethod
    def reservar(self, producto_id: str, cantidad: int, referencia: str) -> str:
        ...

    @abstractmethod
    def confirmar_reserva(self, reserva_id: str, referencia: str, usuario_id: str = "") -> int:
        ...

    @abstractmethod
    def devolver(self, producto_id: str, cantidad: int, referencia: str, usuario_id: str = "") -> int:
        ...

    @abstractmethod
    def stock_disponible(self, producto_id: str) -> int:
        ...

    @abstractmethod
    def verificar_disponibilidad_lote(self, productos: Iterable[dict]) -> dict[str, int]:
        ...

