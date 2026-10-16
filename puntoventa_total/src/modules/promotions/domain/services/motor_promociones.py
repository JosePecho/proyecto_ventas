"""Motor: selecciona la mejor promocion aplicable a un producto."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion
from src.shared.domain.value_objects.monto import Monto


class MotorPromociones:
    ORDEN_PRECEDENCIA = (TipoPromocion.NX1, TipoPromocion.PORCENTAJE, TipoPromocion.MONTO_FIJO, TipoPromocion.PRECIO_ESPECIAL)

    @classmethod
    def vigentes(cls, promociones: Sequence[Promocion], momento: datetime | None = None) -> list[Promocion]:
        return [p for p in promociones if p.esta_vigente(momento)]

    @classmethod
    def mejor_para_producto(
        cls, promociones: Sequence[Promocion], producto_id: str, monto_base: Monto, cantidad: int = 1
    ) -> tuple[Optional[Promocion], Monto]:
        candidatas = [p for p in cls.vigentes(promociones) if p.cubre_producto(producto_id)]
        mejor_promo, mejor_monto = None, Monto(0, monto_base.moneda)
        for promo in sorted(candidatas, key=lambda p: cls.ORDEN_PRECEDENCIA.index(p.tipo)):
            descuento = promo.calcular_descuento(monto_base, cantidad)
            if descuento.valor > mejor_monto.valor:
                mejor_promo, mejor_monto = promo, descuento
        return mejor_promo, mejor_monto

    @classmethod
    def promocion_activa_para(cls, producto_id: str) -> Optional[dict]:
        """Helper estatico usado por el adaptador del POS."""
        from src.modules.promotions.infrastructure.factories import construir_promocion_repository

        for promo in construir_promocion_repository().listar_activas():
            if promo.cubre_producto(producto_id) and promo.esta_vigente():
                return {
                    "id": str(promo.id),
                    "nombre": promo.nombre,
                    "tipo": promo.tipo.value,
                    "descripcion": f"{promo.nombre} ({promo.tipo.value})",
                }
        return None

