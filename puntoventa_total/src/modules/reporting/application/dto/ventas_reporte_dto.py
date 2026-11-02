from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class VentasReporteDTO:
    desde: str
    hasta: str
    por_dia: Sequence[dict]
    total_ventas: float
    total_igv: float
    cantidad_tickets: int

