from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class VentasReporteDTO:
    desde: str
    hasta: str
    por_dia: Sequence[dict]
    total_ventas: float
    total_igv: float
    cantidad_tickets: int

