from dataclasses import dataclass


@dataclass(frozen=True)
class CrearPedidoDTO:
    cliente_nombre: str
    cliente_telefono: str = ""
    cliente_dni: str | None = None
    cliente_id: str | None = None
    observaciones: str = ""
    moneda: str = "PEN"
    cliente_email: str = ""


@dataclass(frozen=True)
class AgregarProductoPedidoDTO:
    pedido_id: str
    producto_id: str
    cantidad: int = 1

