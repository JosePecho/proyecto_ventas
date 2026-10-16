"""Puerto de inventario para pedidos (reserva -> confirmacion de salida)."""
from abc import ABC, abstractmethod


class InventarioPort(ABC):
    @abstractmethod
    def reservar(self, producto_id: str, cantidad: int, referencia: str) -> str:
        ...

    @abstractmethod
    def confirmar_reserva(self, reserva_id: str, referencia: str, usuario_id: str = "") -> int:
        ...

    @abstractmethod
    def liberar(self, reserva_id: str) -> None:
        ...

    @abstractmethod
    def stock_disponible(self, producto_id: str) -> int:
        ...

    @abstractmethod
    def devolver(self, producto_id: str, cantidad: int, referencia: str, usuario_id: str = "") -> int:
        ...

