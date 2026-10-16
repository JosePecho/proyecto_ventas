from typing import Sequence

from src.modules.cash_register.application.ports.ventas_turno_port import VentasTurnoPort


class VentasTurnoAdapter(VentasTurnoPort):
    """Consolida las ventas del turno directamente desde los modelos de sales."""

    def total_ventas(self, turno_id: str) -> float:
        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel

        total = (
            VentaModel.objects.filter(turno_caja_id=turno_id, estado=EstadoVenta.PAGADA.value)
            .values_list("total", flat=True)
        )
        return float(sum(total))

    def pagos_del_turno(self, turno_id: str) -> Sequence[dict]:
        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel

        return list(
            PagoModel.objects.filter(
                venta__turno_caja_id=turno_id,
                venta__estado=EstadoVenta.PAGADA.value,
            ).values("metodo", "monto")
        )

    def contar_ventas(self, turno_id: str) -> int:
        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel

        return VentaModel.objects.filter(
            turno_caja_id=turno_id, estado=EstadoVenta.PAGADA.value
        ).count()

