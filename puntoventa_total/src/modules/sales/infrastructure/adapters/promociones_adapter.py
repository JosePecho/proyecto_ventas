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

        from src.modules.promotions.infrastructure.adapters.frecuencia_cliente_adapter import FrecuenciaClienteAdapter
        repo = construir_promocion_repository()
        frecuencia = AplicarDescuentoFrecuencia(repo, FrecuenciaClienteAdapter()).ejecutar(cliente_id, subtotal) if cliente_id else Monto(0, subtotal.moneda)
        candidatas_combo = [p for p in repo.listar_activas() if p.tipo.value == "COMBO" and p.esta_vigente()]
        if frecuencia.valor == 0 and not candidatas_combo:
            return Monto(0, subtotal.moneda)
        from src.modules.sales.infrastructure.factories import construir_venta_repository
        agregado = construir_venta_repository().buscar_por_id(venta_id)
        combos = [p.descuento_combo(agregado.lineas).valor for p in candidatas_combo] if agregado else []
        descuentos_linea = sum((l.descuento.valor for l in agregado.lineas), 0) if agregado else 0
        mejor = max([frecuencia.valor, descuentos_linea] + combos)
        return Monto(max(0, mejor - descuentos_linea), subtotal.moneda)

    def promocion_aplicable(self, producto_id: str) -> Optional[dict]:
        from src.modules.promotions.domain.services.motor_promociones import MotorPromociones

        return MotorPromociones.promocion_activa_para(producto_id)

