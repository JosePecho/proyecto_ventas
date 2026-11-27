from dataclasses import dataclass


@dataclass(frozen=True)
class PagoDTO:
    venta_id: str
    metodo: str
    monto: float
    vuelto: float | None = None
    referencia: str = ""

