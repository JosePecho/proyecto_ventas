from dataclasses import dataclass, field

from src.shared.domain.events.domain_event import DomainEvent


@dataclass(frozen=True)
class PedidoListo(DomainEvent):
    pedido_id: str = ""
    numero: str = ""
    entidad: str = field(default="Pedido", repr=False)

