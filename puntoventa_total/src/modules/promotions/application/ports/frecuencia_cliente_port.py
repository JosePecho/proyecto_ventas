"""Puerto al modulo de clientes para descuentos por frecuencia."""
from abc import ABC, abstractmethod


class FrecuenciaClientePort(ABC):
    @abstractmethod
    def clasificacion(self, cliente_id: str) -> str:
        """FRECUENTE | OCASIONAL | SIN_DATOS."""
        ...

    @abstractmethod
    def compras_previas(self, cliente_id: str) -> int:
        ...

