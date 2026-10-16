"""Linea de venta con precio unitario congelado al momento del cobro."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.value_objects.monto import Monto


@dataclass
class DetalleVenta(BaseEntity):
    venta_id: str = ""
    producto_id: str = ""
    producto_nombre: str = ""
    cantidad: int = 1
    precio_unitario: Monto = None
    descuento: Monto = None
    pct_descuento: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        self._requerir(self.producto_id, "producto_id")
        self._requerir(self.producto_nombre, "producto_nombre", 150)
        if self.cantidad <= 0:
            raise ValidationException("La cantidad debe ser mayor a cero")
        if self.precio_unitario is None:
            raise TypeError("DetalleVenta requiere precio_unitario (Monto)")
        if self.descuento is None:
            self.descuento = Monto(0, self.precio_unitario.moneda)

    @property
    def subtotal(self) -> Monto:
        return self.precio_unitario * self.cantidad

    @property
    def total(self) -> Monto:
        return self.subtotal - self.descuento

    def aplicar_descuento_pct(self, pct: Decimal) -> None:
        if pct < 0 or pct > 100:
            raise ValidationException("Descuento entre 0 y 100")
        self.pct_descuento = pct
        self.descuento = self.subtotal.porcentaje(pct)
        self.marcar_actualizado()

    def cambiar_cantidad(self, nueva: int) -> None:
        if nueva <= 0:
            raise ValidationException("La cantidad debe ser mayor a cero")
        self.cantidad = nueva
        self.descuento = self.subtotal.porcentaje(self.pct_descuento)
        self.marcar_actualizado()

from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

