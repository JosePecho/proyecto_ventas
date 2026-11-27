from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate


class PedidoRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, pedido_id) -> PedidoAggregate | None:
        ...

    @abstractmethod
    def buscar_por_numero(self, numero: str) -> PedidoAggregate | None:
        ...

    @abstractmethod
    def guardar(self, agregado: PedidoAggregate) -> PedidoAggregate:
        ...

    @abstractmethod
    def listar_por_cliente(self, cliente_id: str) -> Sequence[PedidoAggregate]:
        ...

    @abstractmethod
    def listar_por_estado(self, estado: str) -> Sequence[PedidoAggregate]:
        ...

    @abstractmethod
    def siguiente_numero(self) -> str:
        ...

