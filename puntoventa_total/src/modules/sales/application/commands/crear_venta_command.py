from dataclasses import dataclass


@dataclass(frozen=True)
class CrearVentaCommand:
    cajero_id: str
    turno_caja_id: str | None = None
    cliente_id: str | None = None
    moneda: str = "PEN"

