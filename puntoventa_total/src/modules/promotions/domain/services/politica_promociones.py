"""Reglas de negocio de promociones (tope de descuento, acumulacion)."""
from __future__ import annotations

from decimal import Decimal

from src.shared.domain.value_objects.monto import Monto


class PoliticaPromociones:
    DESCUENTO_MAXIMO_VENTA = Decimal("50")
    PERMITE_ACUMULAR = False

    @classmethod
    def validar_tope_venta(cls, pct_total: Decimal) -> None:
        if pct_total > cls.DESCUENTO_MAXIMO_VENTA:
            raise ValidationException(
                f"El descuento total ({pct_total}%) supera el maximo permitido ({cls.DESCUENTO_MAXIMO_VENTA}%)"
            )

    @classmethod
    def combinar(cls, monto_base: Monto, descuentos: list[Monto]) -> Monto:
        """Si no se permiten acumular, aplica solo el mayor descuento."""
        if not descuentos:
            return monto_base
        if not cls.PERMITE_ACUMULAR:
            return monto_base - max(descuentos, key=lambda d: d.valor)
        total = sum((d.valor for d in descuentos), Decimal("0"))
        return Monto(max(monto_base.valor - total, Decimal("0")), monto_base.moneda)

from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

