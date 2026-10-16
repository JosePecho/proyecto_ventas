from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CrearVentaCommand:
    cajero_id: str
    turno_caja_id: Optional[str] = None
    cliente_id: Optional[str] = None
    moneda: str = "PEN"

