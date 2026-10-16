from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class InventarioReporteDTO:
    bajo_minimo: Sequence[dict]
    baja_rotacion: Sequence[dict]
    valorizado_total: float

