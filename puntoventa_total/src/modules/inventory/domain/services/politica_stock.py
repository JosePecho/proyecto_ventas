"""Politica de stock: umbrales, PEPS y reglas de merma."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence

from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente


class PoliticaStock:
    UMBRAL_MINIMO = 5
    DIAS_ALERTA_VENCIMIENTO = 30

    @classmethod
    def umbral_minimo(cls) -> int:
        from django.conf import settings

        return getattr(settings, "STOCK_MINIMO_ALERTA", cls.UMBRAL_MINIMO)

    @classmethod
    def dias_alerta_vencimiento(cls) -> int:
        from django.conf import settings

        return getattr(settings, "DIAS_ALERTA_VENCIMIENTO", cls.DIAS_ALERTA_VENCIMIENTO)

    @classmethod
    def planificar_salida_peps(cls, lotes: Sequence[Lote], cantidad: int) -> list[tuple[Lote, int]]:
        """Distribuye una salida entre lotes usando PEPS (vencimiento mas proximo primero)."""
        ordenados = sorted(lotes, key=lambda l: (l.fecha_vencimiento or date.max, l.fecha_recepcion or date.min))
        pendiente = cantidad
        plan: list[tuple[Lote, int]] = []
        for lote in ordenados:
            if pendiente == 0:
                break
            if lote.agotado or lote.vencido():
                continue
            tomar = min(lote.cantidad_restante, pendiente)
            plan.append((lote, tomar))
            pendiente -= tomar
        if pendiente > 0:
            disponible = sum(lote.cantidad_restante for lote in ordenados)
            raise StockInsuficiente(plan[0][0].producto_id if plan else "?", disponible, cantidad)
        return plan

    @classmethod
    def requiere_alerta_vencimiento(cls, lote: Lote) -> bool:
        dias = lote.dias_para_vencer
        return dias is not None and 0 <= dias <= cls.dias_alerta_vencimiento()

    @classmethod
    def puede_registrar_merma(cls, cantidad_restante: int, cantidad_merma: int) -> bool:
        return 0 < cantidad_merma <= cantidad_restante

    @classmethod
    def tipos_que_descuentan(cls) -> set:
        return set(TipoMovimiento) - TipoMovimiento.entradas()

