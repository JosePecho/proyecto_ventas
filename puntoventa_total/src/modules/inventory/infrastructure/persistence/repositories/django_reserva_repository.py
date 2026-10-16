from typing import Optional, Sequence
from django.db import connection
from django.utils import timezone

from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository
from src.modules.inventory.infrastructure.persistence.django_models.reserva_model import ReservaModel


class DjangoReservaRepository(ReservaRepository):
    def _a_dominio(self, m: ReservaModel) -> ReservaStock:
        return ReservaStock(
            id=m.id,
            producto_id=str(m.producto_id),
            cantidad=m.cantidad,
            referencia=m.referencia,
            expira_en=m.expira_en,
            confirmada=m.confirmada,
            liberada=m.liberada,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    def buscar_por_id(self, reserva_id) -> Optional[ReservaStock]:
        qs = ReservaModel.objects.filter(pk=reserva_id)
        if connection.in_atomic_block:
            qs = qs.select_for_update()
        m = qs.first()
        return self._a_dominio(m) if m else None

    def listar_por_referencia(self, referencia: str) -> Sequence[ReservaStock]:
        return [self._a_dominio(m) for m in ReservaModel.objects.filter(referencia=referencia)]

    def listar_activas_expiradas(self) -> Sequence[ReservaStock]:
        qs = ReservaModel.objects.filter(confirmada=False, liberada=False, expira_en__lte=timezone.now())
        return [self._a_dominio(m) for m in qs]

    def guardar(self, reserva: ReservaStock) -> ReservaStock:
        m = ReservaModel.objects.filter(pk=reserva.id).first()
        m = m or ReservaModel(id=reserva.id)
        m.producto_id = reserva.producto_id
        m.cantidad = reserva.cantidad
        m.referencia = reserva.referencia
        m.expira_en = reserva.expira_en
        if m.expira_en is not None and timezone.is_naive(m.expira_en):
            m.expira_en = timezone.make_aware(m.expira_en)
        m.confirmada = reserva.confirmada
        m.liberada = reserva.liberada
        m.activo = reserva.activo
        m.save()
        return reserva

