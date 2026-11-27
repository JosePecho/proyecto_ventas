from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date, timedelta

from django.db import connection

from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.repositories.lote_repository import LoteRepository
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.persistence.mappers.lote_mapper import LoteMapper


class DjangoLoteRepository(LoteRepository):
    def __init__(self):
        self._mapper = LoteMapper()
        self._bloqueados: dict[str, LoteModel] = {}
        self._cache_transaction: tuple[object, ...] | None = None

    @contextmanager
    def cache_scope(self) -> Iterator[None]:
        if not connection.in_atomic_block:
            raise RuntimeError("cache_scope requiere una transacción activa")
        if self._cache_transaction is not None:
            raise RuntimeError("cache_scope ya está activo")
        self._cache_transaction = tuple(connection.atomic_blocks)
        try:
            yield
            self._cache_scope_is_active()
        finally:
            self._bloqueados.clear()
            self._cache_transaction = None

    def _cache_scope_is_active(self) -> bool:
        if self._cache_transaction is None:
            return False
        if (
            not connection.in_atomic_block
            or tuple(connection.atomic_blocks) != self._cache_transaction
        ):
            self._bloqueados.clear()
            raise RuntimeError("cache_scope no puede abarcar varias transacciones")
        return True

    def buscar_por_id(self, lote_id) -> Lote | None:
        qs = LoteModel.objects.filter(pk=lote_id)
        if connection.in_atomic_block:
            qs = qs.select_for_update()
        m = qs.first()
        return self._mapper.a_dominio(m) if m else None

    def listar_por_producto(self, producto_id: str, solo_pendientes: bool = True) -> Sequence[Lote]:
        cache_scope_active = self._cache_scope_is_active()
        qs = LoteModel.objects.filter(producto_id=producto_id, activo=True)
        if connection.in_atomic_block:
            qs = qs.select_for_update()
        if solo_pendientes:
            qs = qs.filter(cantidad_restante__gt=0)
        qs = qs.order_by("fecha_vencimiento", "fecha_recepcion")
        modelos = list(qs)
        if cache_scope_active:
            self._bloqueados.update({str(m.pk): m for m in modelos})
        return [self._mapper.a_dominio(m) for m in modelos]

    def guardar(self, lote: Lote) -> Lote:
        cache_scope_active = self._cache_scope_is_active()
        m = None
        if cache_scope_active:
            m = self._bloqueados.pop(str(lote.id), None)
        if m is None:
            m = LoteModel.objects.filter(pk=lote.id).first()
        self._mapper.a_modelo(lote, m).save()
        return lote

    def lotes_por_vencer(self, dias: int) -> Sequence[Lote]:
        hoy = date.today()
        qs = LoteModel.objects.filter(
            activo=True,
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=hoy + timedelta(days=dias),
            cantidad_restante__gt=0,
        )
        return [self._mapper.a_dominio(m) for m in qs]

    def lotes_vencidos(self) -> Sequence[Lote]:
        qs = LoteModel.objects.filter(activo=True, fecha_vencimiento__lt=date.today(), cantidad_restante__gt=0)
        return [self._mapper.a_dominio(m) for m in qs]

