from datetime import date, timedelta
from typing import Optional, Sequence

from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.repositories.lote_repository import LoteRepository
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.persistence.mappers.lote_mapper import LoteMapper


class DjangoLoteRepository(LoteRepository):
    def __init__(self):
        self._mapper = LoteMapper()

    def buscar_por_id(self, lote_id) -> Optional[Lote]:
        m = LoteModel.objects.filter(pk=lote_id).first()
        return self._mapper.a_dominio(m) if m else None

    def listar_por_producto(self, producto_id: str, solo_pendientes: bool = True) -> Sequence[Lote]:
        qs = LoteModel.objects.filter(producto_id=producto_id)
        if solo_pendientes:
            qs = qs.filter(cantidad_restante__gt=0)
        qs = qs.order_by("fecha_vencimiento", "fecha_recepcion")
        return [self._mapper.a_dominio(m) for m in qs]

    def guardar(self, lote: Lote) -> Lote:
        m = LoteModel.objects.filter(pk=lote.id).first()
        self._mapper.a_modelo(lote, m).save()
        return lote

    def lotes_por_vencer(self, dias: int) -> Sequence[Lote]:
        hoy = date.today()
        qs = LoteModel.objects.filter(
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=hoy + timedelta(days=dias),
            cantidad_restante__gt=0,
        )
        return [self._mapper.a_dominio(m) for m in qs]

    def lotes_vencidos(self) -> Sequence[Lote]:
        qs = LoteModel.objects.filter(fecha_vencimiento__lt=date.today(), cantidad_restante__gt=0)
        return [self._mapper.a_dominio(m) for m in qs]

