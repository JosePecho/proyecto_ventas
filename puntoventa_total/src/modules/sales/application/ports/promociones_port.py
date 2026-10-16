from abc import ABC, abstractmethod
from typing import Optional

from src.shared.domain.value_objects.monto import Monto


class PromocionesPort(ABC):
    @abstractmethod
    def descuento_producto(self, producto_id: str, subtotal_linea: Monto, cantidad: int) -> Monto:
        ...

    @abstractmethod
    def descuento_venta(self, venta_id: str, subtotal: Monto, cliente_id: Optional[str] = None) -> Monto:
        ...

    @abstractmethod
    def promocion_aplicable(self, producto_id: str) -> Optional[dict]:
        ...

