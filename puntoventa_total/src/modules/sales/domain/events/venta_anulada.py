from dataclasses import dataclass, field

from src.shared.domain.events.domain_event import DomainEvent


@dataclass(frozen=True)
class VentaAnulada(DomainEvent):
    venta_id: str = ""
    total: float = 0.0
    motivo: str = ""
    usuario_id: str = ""
    entidad: str = field(default="Venta", repr=False)

