"""Registro inmutable del kardex (nunca se borra, se compensa)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.clock import utc_now


@dataclass
class MovimientoStock(BaseEntity):
    producto_id: str = ""
    tipo: TipoMovimiento = TipoMovimiento.ENTRADA
    cantidad: int = 0
    stock_resultante: int = 0
    referencia: str = ""
    usuario_id: str = ""
    observacion: str = ""
    lote_id: Optional[str] = None
    fecha: datetime = None

    def __post_init__(self) -> None:
        self._requerir(self.producto_id, "producto_id")
        if self.cantidad <= 0:
            raise ValidationException("La cantidad del movimiento debe ser positiva")
        if not isinstance(self.tipo, TipoMovimiento):
            self.tipo = TipoMovimiento(self.tipo)
        self.fecha = self.fecha or utc_now()
        self._validar_coherencia()

    def _validar_coherencia(self) -> None:
        if self.tipo in TipoMovimiento.entradas() and self.stock_resultante < 0:
            raise ValidationException("Una entrada no puede dejar stock negativo")

    def es_entrada(self) -> bool:
        return self.tipo in TipoMovimiento.entradas()

    def signo(self) -> int:
        return 1 if self.es_entrada() else -1

from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

