from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProcesarPagoCommand:
    venta_id: str
    metodo: str
    monto: float
    monto_entregado: Optional[float] = None
    referencia: str = ""

