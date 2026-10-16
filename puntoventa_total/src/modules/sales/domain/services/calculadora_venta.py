"""Reglas de calculo de totales, descuentos y cambio."""
from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.sales.domain.exceptions.venta_exceptions import PagoInsuficiente
from src.shared.domain.value_objects.monto import Monto


class CalculadoraVenta:
    IGV_PCT = Decimal("0.18")  # precios incluyen IGV

    @classmethod
    def subtotal(cls, lineas: Sequence[DetalleVenta]) -> Monto:
        if not lineas:
            return Monto(0)
        moneda = lineas[0].precio_unitario.moneda
        total = sum((l.subtotal.valor for l in lineas), Decimal("0"))
        return Monto(total, moneda)

    @classmethod
    def descuentos(cls, lineas: Sequence[DetalleVenta]) -> Monto:
        if not lineas:
            return Monto(0)
        moneda = lineas[0].precio_unitario.moneda
        total = sum((l.descuento.valor for l in lineas), Decimal("0"))
        return Monto(total, moneda)

    @classmethod
    def total(cls, lineas: Sequence[DetalleVenta], descuento_venta: Monto | None = None) -> Monto:
        total = cls.subtotal(lineas) - cls.descuentos(lineas)
        if descuento_venta:
            total = total - descuento_venta
        return total

    @classmethod
    def desglose_igv(cls, total: Monto) -> dict:
        base = Monto((total.valor / (1 + cls.IGV_PCT)).quantize(Decimal("0.01")), total.moneda)
        igv = total - base
        return {"base_imponible": base.a_float(), "igv": igv.a_float(), "total": total.a_float()}

    @classmethod
    def vuelto(cls, total: Monto, pagado: Monto) -> Monto:
        diferencia = pagado.valor - total.valor
        if diferencia < 0:
            raise PagoInsuficiente(float(-diferencia))
        return Monto(diferencia, total.moneda)

    @classmethod
    def calcular_linea(cls, cantidad: int, precio_unitario: Monto, pct_descuento: Decimal = Decimal("0")) -> DetalleVenta:
        raise NotImplementedError("Use DetalleVenta.directo() para crear lineas")

