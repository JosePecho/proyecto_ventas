from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CrearVentaDTO:
    cajero_id: str
    turno_caja_id: Optional[str] = None
    cliente_id: Optional[str] = None
    moneda: str = "PEN"


@dataclass(frozen=True)
class AgregarProductoDTO:
    venta_id: str
    producto_id: str
    cantidad: int = 1


@dataclass(frozen=True)
class ProcesarPagoDTO:
    venta_id: str
    metodo: str
    monto: float
    monto_entregado: Optional[float] = None
    referencia: str = ""

