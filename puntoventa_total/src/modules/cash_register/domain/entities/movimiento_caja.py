"""Movimiento de caja: ingreso/egreso/retiro con firma."""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.value_objects.monto import Monto

TIPOS_MOVIMIENTO = ("VENTA", "RETIRO", "DEPOSITO", "ARQUEO_DIFERENCIA", "NOTA_CREDITO")


@dataclass
class MovimientoCaja(BaseEntity):
    turno_id: str = ""
    tipo: str = "VENTA"
    monto: Monto = None
    referencia: str = ""
    usuario_id: str = ""
    observacion: str = ""

    def __post_init__(self) -> None:
        self._requerir(self.turno_id, "turno_id")
        if self.tipo not in TIPOS_MOVIMIENTO:
            raise MovimientoInvalido(f"Tipo de movimiento invalido: {self.tipo}")
        if self.monto is None:
            raise TypeError("MovimientoCaja requiere un Monto")
        if self.monto.es_cero():
            raise MovimientoInvalido("El monto del movimiento no puede ser cero")

    @property
    def es_ingreso(self) -> bool:
        return self.tipo in ("VENTA", "DEPOSITO")

    @property
    def es_egreso(self) -> bool:
        return self.tipo in ("RETIRO", "NOTA_CREDITO")

    def firmar(self, usuario_id: str) -> None:
        self.usuario_id = usuario_id
        self.marcar_actualizado()

from src.modules.cash_register.domain.exceptions.caja_exceptions import MovimientoInvalido  # noqa: E402

