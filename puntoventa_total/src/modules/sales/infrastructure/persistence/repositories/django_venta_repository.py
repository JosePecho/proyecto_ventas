from datetime import date, datetime, time, timedelta
from typing import Optional, Sequence

from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.infrastructure.persistence.mappers.venta_mapper import VentaMapper


class DjangoVentaRepository(VentaRepository):
    def buscar_por_id(self, venta_id) -> Optional[VentaAggregate]:
        m = VentaModel.objects.filter(pk=venta_id).prefetch_related("detalles", "pagos").first()
        return VentaMapper.agregado_a_dominio(m) if m else None

    def buscar_por_numero_ticket(self, numero_ticket: str) -> Optional[VentaAggregate]:
        m = (
            VentaModel.objects.filter(numero_ticket=numero_ticket)
            .prefetch_related("detalles", "pagos")
            .first()
        )
        return VentaMapper.agregado_a_dominio(m) if m else None

    def guardar(self, agregado: VentaAggregate) -> VentaAggregate:
        VentaMapper.guardar_agregado(agregado)
        return agregado

    def listar_por_turno(self, turno_caja_id: str) -> Sequence[VentaAggregate]:
        qs = (
            VentaModel.objects.filter(turno_caja_id=turno_caja_id)
            .prefetch_related("detalles", "pagos")
            .order_by("fecha_creacion")
        )
        return [VentaMapper.agregado_a_dominio(m) for m in qs]

    def listar_por_fecha(self, desde, hasta) -> Sequence[VentaAggregate]:
        inicio = datetime.combine(desde, time.min) if isinstance(desde, date) else desde
        fin = datetime.combine(hasta, time.max) if isinstance(hasta, date) else hasta
        qs = (
            VentaModel.objects.filter(fecha_creacion__range=(inicio, fin))
            .prefetch_related("detalles", "pagos")
            .order_by("-fecha_creacion")
        )
        return [VentaMapper.agregado_a_dominio(m) for m in qs]

    def siguiente_numero_ticket(self) -> str:
        total_hoy = VentaModel.objects.filter(fecha_creacion__date=date.today()).count()
        return f"T{date.today():%Y%m%d}{total_hoy + 1:05d}"

