from typing import Optional, Sequence

from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.enums.estado_promocion import EstadoPromocion
from src.modules.promotions.domain.repositories.promocion_repository import PromocionRepository
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.promotions.infrastructure.persistence.mappers.promocion_mapper import PromocionMapper


class DjangoPromocionRepository(PromocionRepository):
    def __init__(self):
        self._mapper = PromocionMapper()

    def buscar_por_id(self, promocion_id) -> Optional[Promocion]:
        m = PromocionModel.objects.filter(pk=promocion_id).first()
        return self._mapper.a_dominio(m) if m else None

    def listar(self, incluir_finalizadas: bool = False) -> Sequence[Promocion]:
        qs = PromocionModel.objects.filter(activo=True)
        if not incluir_finalizadas:
            qs = qs.exclude(estado__in=[EstadoPromocion.FINALIZADA.value, EstadoPromocion.CANCELADA.value])
        return [self._mapper.a_dominio(m) for m in qs]

    def listar_activas(self) -> Sequence[Promocion]:
        qs = PromocionModel.objects.filter(activo=True, estado=EstadoPromocion.ACTIVA.value)
        return [self._mapper.a_dominio(m) for m in qs]

    def activa_para_producto(self, producto_id: str) -> Optional[Promocion]:
        from django.utils import timezone

        m = (
            PromocionModel.objects.filter(
                activo=True,
                estado=EstadoPromocion.ACTIVA.value,
                producto_id=producto_id,
            )
            .filter(vigencia_desde__lte=timezone.now())
            .filter(vigencia_hasta__gte=timezone.now())
            .first()
        )
        return self._mapper.a_dominio(m) if m else None

    def guardar(self, promocion: Promocion) -> Promocion:
        m = PromocionModel.objects.filter(pk=promocion.id).first()
        self._mapper.a_modelo(promocion, m).save()
        return promocion

