from dataclasses import dataclass

from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.value_objects.monto import Monto


@dataclass
class DetallePedido(BaseEntity):
    pedido_id: str = ""
    producto_id: str = ""
    producto_nombre: str = ""
    cantidad: int = 1
    precio_unitario: Monto = None
    subtotal: Monto = None
    requiere_stock: bool = True

    def __post_init__(self) -> None:
        self._requerir(self.producto_id, "producto_id")
        self._requerir(self.producto_nombre, "producto_nombre", 150)
        if self.cantidad <= 0:
            raise ValidationException("La cantidad debe ser mayor a cero")
        if self.precio_unitario is None:
            raise TypeError("DetallePedido requiere precio_unitario")
        self.subtotal = self.precio_unitario * self.cantidad

    def cambiar_cantidad(self, nueva: int) -> None:
        if nueva <= 0:
            raise ValidationException("La cantidad debe ser mayor a cero")
        self.cantidad = nueva
        self.subtotal = self.precio_unitario * nueva
        self.marcar_actualizado()

from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

