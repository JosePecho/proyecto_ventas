"""Registra ingresos/egresos de caja (retiros, depósitos, notas)."""
from __future__ import annotations

from src.modules.cash_register.domain.entities.movimiento_caja import MovimientoCaja
from src.modules.cash_register.domain.exceptions.caja_exceptions import TurnoNoEncontrado
from src.modules.cash_register.domain.repositories.turno_repository import TurnoRepository
from src.shared.domain.value_objects.monto import Monto


class RegistrarMovimiento:
    def __init__(self, repo: TurnoRepository, moneda: str = "PEN"):
        self._repo = repo
        self._moneda = moneda

    def ejecutar(
        self,
        turno_id: str,
        tipo: str,
        monto: float,
        usuario_id: str,
        referencia: str = "",
        observacion: str = "",
    ) -> dict:
        turno = self._repo.buscar_por_id(turno_id)
        if turno is None:
            raise TurnoNoEncontrado(turno_id)

        movimiento = MovimientoCaja(
            turno_id=turno_id,
            tipo=tipo,
            monto=Monto(abs(monto), self._moneda),
            referencia=referencia,
            observacion=observacion,
        )
        movimiento.firmar(usuario_id)
        self._repo.registrar_movimiento(movimiento)
        return {"movimiento_id": str(movimiento.id), "tipo": tipo, "monto": abs(monto)}

