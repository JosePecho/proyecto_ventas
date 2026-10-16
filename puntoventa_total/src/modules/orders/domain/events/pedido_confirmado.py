from dataclasses import dataclass, field

from src.shared.domain.events.domain_event import DomainEvent


@dataclass(frozen=True)
class PedidoConfirmado(DomainEvent):
    pedido_id: str = ""
    total: float = 0.0
    entidad: str = field(default="Pedido", repr=False)

