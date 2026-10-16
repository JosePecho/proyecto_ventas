from dataclasses import dataclass, field

from src.shared.domain.events.domain_event import DomainEvent


@dataclass(frozen=True)
class StockActualizado(DomainEvent):
    producto_id: str = ""
    stock_anterior: int = 0
    stock_nuevo: int = 0
    tipo_movimiento: str = ""
    entidad: str = field(default="Existencia", repr=False)

