"""Cierra el turno comparando el conteo fisico contra el saldo del sistema."""
from __future__ import annotations

from src.modules.cash_register.application.dto.arqueo_dto import ArqueoDTO
from src.modules.cash_register.application.ports.ventas_turno_port import VentasTurnoPort
from src.modules.cash_register.domain.entities.movimiento_caja import MovimientoCaja
from src.modules.cash_register.domain.exceptions.caja_exceptions import TurnoNoEncontrado
from src.modules.cash_register.domain.repositories.turno_repository import TurnoRepository
from src.modules.cash_register.domain.services.calculadora_arqueo import CalculadoraArqueo
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork
from src.shared.domain.value_objects.monto import Monto


class CerrarTurno:
    def __init__(
        self,
        repo: TurnoRepository,
        ventas: VentasTurnoPort,
        moneda: str = "PEN",
        uow: UnitOfWork | None = None,
    ):
        self._repo = repo
        self._ventas = ventas
        self._moneda = moneda
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, turno_id: str, monto_fisico: float, usuario_id: str, observaciones: str = "") -> ArqueoDTO:
        with self._uow:
            turno = self._repo.buscar_por_id(turno_id)
            if turno is None:
                raise TurnoNoEncontrado(turno_id)

            movimientos = self._repo.movimientos_del_turno(turno_id)
            saldo_sistema = CalculadoraArqueo.saldo_sistema(turno.monto_apertura, movimientos)
            diferencia = turno.registrar_cierre(Monto(monto_fisico, self._moneda), saldo_sistema)
            turno.observaciones = observaciones

            # La diferencia (faltante/sobrante) queda como movimiento firmado
            if not CalculadoraArqueo.es_congruente(diferencia):
                movimiento = MovimientoCaja(
                    turno_id=turno_id,
                    tipo="ARQUEO_DIFERENCIA",
                    monto=Monto(abs(diferencia.valor), self._moneda),
                    observacion=f"Diferencia de arqueo: {diferencia}",
                )
                movimiento.firmar(usuario_id)
                self._repo.registrar_movimiento(movimiento)

            self._repo.guardar(turno)
            return ConsultarArqueo(self._repo, self._ventas).ejecutar(turno_id)

from src.modules.cash_register.application.use_cases.consultar_arqueo import ConsultarArqueo  # noqa: E402

