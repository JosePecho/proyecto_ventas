from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate


class VentaRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, venta_id) -> Optional[VentaAggregate]:
        ...

    @abstractmethod
    def buscar_por_numero_ticket(self, numero_ticket: str) -> Optional[VentaAggregate]:
        ...

    @abstractmethod
    def guardar(self, agregado: VentaAggregate) -> VentaAggregate:
        ...

    @abstractmethod
    def listar_por_turno(self, turno_caja_id: str) -> Sequence[VentaAggregate]:
        ...

    @abstractmethod
    def listar_por_fecha(self, desde, hasta) -> Sequence[VentaAggregate]:
        ...

    @abstractmethod
    def siguiente_numero_ticket(self) -> str:
        ...

