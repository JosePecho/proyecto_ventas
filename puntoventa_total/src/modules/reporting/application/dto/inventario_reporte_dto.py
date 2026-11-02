from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class InventarioReporteDTO:
    bajo_minimo: Sequence[dict]
    baja_rotacion: Sequence[dict]
    valorizado_total: float

