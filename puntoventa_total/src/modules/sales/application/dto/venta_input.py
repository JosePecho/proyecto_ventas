from dataclasses import dataclass


@dataclass(frozen=True)
class CrearVentaDTO:
    cajero_id: str
    turno_caja_id: str | None = None
    cliente_id: str | None = None
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
    monto_entregado: float | None = None
    referencia: str = ""

