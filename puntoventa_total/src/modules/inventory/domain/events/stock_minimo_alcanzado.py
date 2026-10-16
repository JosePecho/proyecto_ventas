from dataclasses import dataclass, field

from src.shared.domain.events.domain_event import DomainEvent


@dataclass(frozen=True)
class StockMinimoAlcanzado(DomainEvent):
    producto_id: str = ""
    stock_actual: int = 0
    umbral: int = 0
    entidad: str = field(default="Existencia", repr=False)

