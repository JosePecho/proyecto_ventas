from datetime import date
from typing import Sequence

from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.infrastructure.persistence.django_models.movimiento_model import MovimientoModel
from src.modules.inventory.infrastructure.persistence.mappers.movimiento_mapper import MovimientoMapper


class DjangoMovimientoRepository(MovimientoRepository):
    def __init__(self):
        self._mapper = MovimientoMapper()

    def guardar(self, movimiento: MovimientoStock) -> MovimientoStock:
        m = MovimientoModel.objects.filter(pk=movimiento.id).first()
        self._mapper.a_modelo(movimiento, m).save(force_insert=m is None)
        return movimiento

    def _kardex_queryset(self, producto_id: str, desde=None, hasta=None):
        qs = MovimientoModel.objects.filter(producto_id=producto_id)
        if isinstance(desde, date):
            qs = qs.filter(fecha__date__gte=desde)
        if isinstance(hasta, date):
            qs = qs.filter(fecha__date__lte=hasta)
        return qs

    def contar_kardex(self, producto_id: str, desde=None, hasta=None) -> int:
        return self._kardex_queryset(producto_id, desde, hasta).count()

    def kardex(self, producto_id: str, desde=None, hasta=None, limite: int | None = 200) -> Sequence[MovimientoStock]:
        qs = self._kardex_queryset(producto_id, desde, hasta)
        return [self._mapper.a_dominio(m) for m in qs.order_by("-fecha", "-id")[:limite]]

    def total_entradas(self, producto_id: str) -> int:
        from django.db.models import Sum

        from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento

        entradas = TipoMovimiento.entradas()
        total = (
            MovimientoModel.objects.filter(producto_id=producto_id, tipo__in=[t.value for t in entradas])
            .aggregate(total=Sum("cantidad"))["total"]
        )
        return total or 0

