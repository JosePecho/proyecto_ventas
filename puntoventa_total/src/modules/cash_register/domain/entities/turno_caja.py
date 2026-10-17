"""Turno de caja: apertura, arqueo y cierre."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.modules.cash_register.domain.enums.estado_turno import EstadoTurno
from src.modules.cash_register.domain.exceptions.caja_exceptions import TurnoYaCerrado
from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.clock import utc_now
from src.shared.domain.value_objects.monto import Monto


@dataclass
class TurnoCaja(BaseEntity):
    cajero_id: str = ""
    estado: EstadoTurno = EstadoTurno.ABIERTO
    monto_apertura: Monto = None
    monto_cierre: Optional[Monto] = None
    monto_sistema: Optional[Monto] = None
    diferencia: Optional[Monto] = None
    fecha_apertura: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    observaciones: str = ""

    def __post_init__(self) -> None:
        self._requerir(self.cajero_id, "cajero_id")
        if self.monto_apertura is None:
            raise TypeError("TurnoCaja requiere monto de apertura")
        if not isinstance(self.estado, EstadoTurno):
            self.estado = EstadoTurno(self.estado)
        self.fecha_apertura = self.fecha_apertura or utc_now()

    @property
    def esta_abierto(self) -> bool:
        return self.estado == EstadoTurno.ABIERTO

    def registrar_cierre(self, monto_fisico: Monto, monto_sistema: Monto) -> Monto:
        if not self.esta_abierto:
            raise TurnoYaCerrado()
        self.monto_cierre = monto_fisico
        self.monto_sistema = monto_sistema
        self.diferencia = monto_fisico - monto_sistema
        self.estado = EstadoTurno.CERRADO
        self.fecha_cierre = utc_now()
        self.marcar_actualizado()
        return self.diferencia

    def saldo_esperado(self, ingresos: Monto, egresos: Monto) -> Monto:
        return self.monto_apertura + ingresos - egresos

