"""Analitica simple de frecuencia de compra del cliente."""
from __future__ import annotations

from datetime import datetime
from typing import Sequence


class FrecuenciaCompra:
    @classmethod
    def dias_entre_compras(cls, fechas: Sequence[datetime]) -> float:
        ordenadas = sorted(f for f in fechas if f)
        if len(ordenadas) < 2:
            return 0.0
        diferencias = [(b - a).days for a, b in zip(ordenadas, ordenadas[1:])]
        return round(sum(diferencias) / len(diferencias), 2)

    @classmethod
    def clasificar(cls, dias_promedio: float) -> str:
        if dias_promedio == 0:
            return "SIN_DATOS"
        if dias_promedio <= 7:
            return "FRECUENTE"
        if dias_promedio <= 30:
            return "OCASIONAL"
        return "OCASIONAL"

    @classmethod
    def ultimo_intervalo(cls, fechas: Sequence[datetime]) -> float:
        ordenadas = sorted(f for f in fechas if f)
        if len(ordenadas) < 2:
            return 0.0
        return (ordenadas[-1] - ordenadas[-2]).days

