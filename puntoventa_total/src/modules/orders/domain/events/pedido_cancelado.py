from dataclasses import dataclass, field

from src.shared.domain.events.domain_event import DomainEvent


@dataclass(frozen=True)
class PedidoCancelado(DomainEvent):
    pedido_id: str = ""
    motivo: str = ""
    usuario_id: str = ""
    entidad: str = field(default="Pedido", repr=False)

