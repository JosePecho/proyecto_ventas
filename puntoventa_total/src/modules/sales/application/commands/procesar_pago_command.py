from dataclasses import dataclass


@dataclass(frozen=True)
class ProcesarPagoCommand:
    venta_id: str
    metodo: str
    monto: float
    monto_entregado: float | None = None
    referencia: str = ""

