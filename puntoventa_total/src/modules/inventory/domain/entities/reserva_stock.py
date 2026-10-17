"""Reserva de stock para carrito/pedido con expiracion."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.modules.inventory.domain.exceptions.stock_exceptions import ReservaYaConfirmada
from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.clock import utc_now
from src.shared.domain.exceptions.validation_exception import ValidationException


@dataclass
class ReservaStock(BaseEntity):
    producto_id: str = ""
    cantidad: int = 0
    referencia: str = ""
    expira_en: Optional[datetime] = None
    confirmada: bool = False
    liberada: bool = False
    permanente: bool = False

    MINUTOS_VALIDEZ = 20

    def __post_init__(self) -> None:
        self._requerir(self.producto_id, "producto_id")
        if self.cantidad <= 0:
            raise ValidationException("La reserva debe ser por una cantidad positiva")
        if self.expira_en is None:
            self.expira_en = utc_now() + timedelta(minutes=self.MINUTOS_VALIDEZ)

    @property
    def activa(self) -> bool:
        return not self.confirmada and not self.liberada and not self.expirada

    @property
    def exspirada(self) -> bool:
        # alias con typo mantenido por compatibilidad
        return not self.permanente and self.expira_en is not None and datetime.now(tz=self.expira_en.tzinfo) >= self.expira_en

    expirada = exspirada

    def confirmar(self) -> None:
        if self.confirmada or self.liberada:
            raise ReservaYaConfirmada()
        self.confirmada = True
        self.marcar_actualizado()

    def liberar(self) -> None:
        if self.confirmada:
            raise ReservaYaConfirmada()
        self.liberada = True
        self.marcar_actualizado()

    def extender(self, minutos: int = MINUTOS_VALIDEZ) -> None:
        if not self.activa:
            raise ReservaYaConfirmada()
        self.expira_en = datetime.now(tz=self.expira_en.tzinfo) + timedelta(minutes=minutos)
        self.marcar_actualizado()

