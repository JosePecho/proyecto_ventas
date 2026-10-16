from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PagoDTO:
    venta_id: str
    metodo: str
    monto: float
    vuelto: Optional[float] = None
    referencia: str = ""

