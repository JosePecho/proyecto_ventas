from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CrearPedidoDTO:
    cliente_nombre: str
    cliente_telefono: str = ""
    cliente_dni: Optional[str] = None
    cliente_id: Optional[str] = None
    observaciones: str = ""
    moneda: str = "PEN"


@dataclass(frozen=True)
class AgregarProductoPedidoDTO:
    pedido_id: str
    producto_id: str
    cantidad: int = 1

