"""Lote de ingreso: cantidad, proveedor, vencimiento y costo."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.value_objects.monto import Monto


@dataclass
class Lote(BaseEntity):
    producto_id: str = ""
    numero_lote: str = ""
    cantidad_inicial: int = 0
    cantidad_restante: int = 0
    costo_unitario: Optional[Monto] = None
    proveedor: str = ""
    fecha_vencimiento: Optional[date] = None
    fecha_recepcion: Optional[date] = None

    def __post_init__(self) -> None:
        self._requerir(self.producto_id, "producto_id")
        self._requerir(self.numero_lote, "numero_lote", 40)
        if self.cantidad_inicial <= 0:
            raise ValidationException("La cantidad inicial del lote debe ser positiva")
        if self.cantidad_restante > self.cantidad_inicial:
            raise ValidationException("La cantidad restante no puede superar la inicial")
        self.fecha_recepcion = self.fecha_recepcion or date.today()

    @property
    def agotado(self) -> bool:
        return self.cantidad_restante == 0

    @property
    def dias_para_vencer(self) -> Optional[int]:
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - date.today()).days

    def descontar(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValidationException("Cantidad a descontar invalida")
        if self.cantidad_restante < cantidad:
            raise StockInsuficiente(self.producto_id, self.cantidad_restante, cantidad)
        self.cantidad_restante -= cantidad
        self.marcar_actualizado()

    def vencido(self) -> bool:
        dias = self.dias_para_vencer
        return dias is not None and dias < 0

from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente  # noqa: E402
from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

