from typing import Sequence

from src.modules.customers.application.ports.historial_compras_port import HistorialComprasPort


class HistorialComprasAdapter(HistorialComprasPort):
    """Lee las ventas pagadas del cliente desde el modulo sales."""

    def compras_del_cliente(self, cliente_id: str) -> Sequence[dict]:
        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel

        ventas = VentaModel.objects.filter(
            cliente_id=cliente_id, estado=EstadoVenta.PAGADA.value
        ).order_by("-fecha_creacion")
        return [
            {"fecha": v.fecha_creacion, "total": float(v.total), "numero_ticket": v.numero_ticket}
            for v in ventas
        ]

    def total_gastado(self, cliente_id: str) -> float:
        from django.db.models import Sum

        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel

        total = (
            VentaModel.objects.filter(cliente_id=cliente_id, estado=EstadoVenta.PAGADA.value)
            .aggregate(total=Sum("total"))["total"]
        )
        return float(total or 0)

