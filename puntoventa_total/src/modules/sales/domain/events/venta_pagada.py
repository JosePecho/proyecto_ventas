from dataclasses import dataclass, field

from src.shared.domain.events.domain_event import DomainEvent


@dataclass(frozen=True)
class VentaPagada(DomainEvent):
    venta_id: str = ""
    total: float = 0.0
    cajero_id: str = ""
    entidad: str = field(default="Venta", repr=False)

