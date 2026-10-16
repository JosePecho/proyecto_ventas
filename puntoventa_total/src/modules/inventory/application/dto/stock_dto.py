from dataclasses import dataclass


@dataclass(frozen=True)
class StockDTO:
    producto_id: str
    cantidad: int
    reservada: int
    disponible: int
    bajo_minimo: bool


@dataclass(frozen=True)
class AjusteStockDTO:
    producto_id: str
    cantidad: int
    usuario_id: str
    observacion: str = ""

