from typing import Optional

from src.modules.sales.application.ports.promociones_port import PromocionesPort
from src.shared.domain.value_objects.monto import Monto


class PromocionesAdapter(PromocionesPort):
    """Consulta el motor de promociones del modulo promotions."""

    def descuento_producto(self, producto_id: str, subtotal_linea: Monto, cantidad: int) -> Monto:
        from src.modules.promotions.application.use_cases.calcular_descuento import CalcularDescuento
        from src.modules.promotions.infrastructure.factories import construir_promocion_repository

        try:
            return CalcularDescuento(construir_promocion_repository()).por_producto(
                producto_id, subtotal_linea, cantidad
            )
        except Exception:
            return Monto(0, subtotal_linea.moneda)

    def descuento_venta(self, venta_id: str, subtotal: Monto, cliente_id: Optional[str] = None) -> Monto:
        from src.modules.promotions.application.use_cases.aplicar_descuento_frecuencia import (
            AplicarDescuentoFrecuencia,
        )
        from src.modules.promotions.infrastructure.factories import construir_promocion_repository

        if not cliente_id:
            return Monto(0, subtotal.moneda)
        try:
            return AplicarDescuentoFrecuencia(construir_promocion_repository()).ejecutar(cliente_id, subtotal)
        except Exception:
            return Monto(0, subtotal.moneda)

    def promocion_aplicable(self, producto_id: str) -> Optional[dict]:
        from src.modules.promotions.domain.services.motor_promociones import MotorPromociones

        return MotorPromociones.promocion_activa_para(producto_id)

