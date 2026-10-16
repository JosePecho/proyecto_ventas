"""Calculo del arqueo y diferencias por metodo de pago."""
from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from src.modules.cash_register.domain.entities.movimiento_caja import MovimientoCaja
from src.shared.domain.value_objects.monto import Monto


class CalculadoraArqueo:
    @classmethod
    def ingresos(cls, movimientos: Sequence[MovimientoCaja]) -> Monto:
        if not movimientos:
            return Monto(0)
        moneda = movimientos[0].monto.moneda
        total = sum((m.monto.valor for m in movimientos if m.es_ingreso), Decimal("0"))
        return Monto(total, moneda)

    @classmethod
    def egresos(cls, movimientos: Sequence[MovimientoCaja]) -> Monto:
        if not movimientos:
            return Monto(0)
        moneda = movimientos[0].monto.moneda
        total = sum((m.monto.valor for m in movimientos if m.es_egreso), Decimal("0"))
        return Monto(total, moneda)

    @classmethod
    def saldo_sistema(cls, monto_apertura: Monto, movimientos: Sequence[MovimientoCaja]) -> Monto:
        return monto_apertura + cls.ingresos(movimientos) - cls.egresos(movimientos)

    @classmethod
    def diferencia(cls, monto_fisico: Monto, monto_sistema: Monto) -> Monto:
        return monto_fisico - monto_sistema

    @classmethod
    def es_congruente(cls, diferencia: Monto, tolerancia: Decimal = Decimal("0.05")) -> bool:
        return abs(diferencia.valor) <= tolerancia

    @classmethod
    def desglose_por_metodo(cls, pagos: Sequence[dict]) -> dict[str, Decimal]:
        """Consolida totales por metodo de pago para el arqueo."""
        desglose: dict[str, Decimal] = {}
        for pago in pagos:
            tipo = pago.get("metodo", "DESCONOCIDO")
            desglose[tipo] = desglose.get(tipo, Decimal("0")) + Decimal(str(pago.get("monto", 0)))
        return desglose

