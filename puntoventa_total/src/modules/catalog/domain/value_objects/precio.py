"""Precio de venta: monto + costo + margen minimo configurable."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto


@dataclass(frozen=True)
class Precio:
    costo: Monto
    venta: Monto
    margen_minimo_pct: Decimal = Decimal("10")

    def __post_init__(self) -> None:
        if self.venta.es_cero():
            raise ValidationException("El precio de venta no puede ser cero")
        margen = self.margen_pct()
        if margen < self.margen_minimo_pct:
            raise ValidationException(
                f"El margen ({margen}%) es inferior al minimo requerido ({self.margen_minimo_pct}%)"
            )

    def margen_pct(self) -> Decimal:
        if self.costo.es_cero():
            return Decimal("100")
        return ((self.venta.valor - self.costo.valor) / self.costo.valor * Decimal("100")).quantize(
            Decimal("0.01")
        )

    def ganancia_unitaria(self) -> Monto:
        return self.venta - self.costo

    def aplicar_descuento_pct(self, pct: Decimal) -> Monto:
        descuento = self.venta.porcentaje(pct)
        nuevo = self.venta - descuento
        if nuevo.valor < self.costo.valor:
            raise ValidationException("El descuento dejaria al producto por debajo del costo")
        return nuevo

