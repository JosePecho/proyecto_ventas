from abc import ABC, abstractmethod
from typing import Sequence


class TicketPort(ABC):
    @abstractmethod
    def emitir(self, venta: dict, lineas: Sequence[dict], pagos: Sequence[dict]) -> bytes:
        """Devuelve el ticket en PDF (bytes)."""
        ...

    @abstractmethod
    def nombre_archivo(self, numero_ticket: str) -> str:
        ...

