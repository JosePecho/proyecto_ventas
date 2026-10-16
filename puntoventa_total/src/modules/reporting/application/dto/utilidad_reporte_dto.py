from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class UtilidadReporteDTO:
    desde: str
    hasta: str
    por_producto: Sequence[dict]
    ingresos_totales: float
    costos_totales: float
    utilidad_total: float
    margen_pct: float

