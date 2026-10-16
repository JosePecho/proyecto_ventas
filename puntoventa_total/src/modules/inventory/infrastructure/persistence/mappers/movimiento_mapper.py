import uuid
from django.utils import timezone

from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.infrastructure.persistence.django_models.movimiento_model import MovimientoModel


class MovimientoMapper:
    @staticmethod
    def a_dominio(m: MovimientoModel) -> MovimientoStock:
        return MovimientoStock(
            id=m.id,
            producto_id=str(m.producto_id),
            tipo=TipoMovimiento(m.tipo),
            cantidad=m.cantidad,
            stock_resultante=m.stock_resultante,
            referencia=m.referencia,
            usuario_id=str(m.usuario_id) if m.usuario_id else "",
            observacion=m.observacion,
            lote_id=str(m.lote_id) if m.lote_id else None,
            fecha=m.fecha,
            fecha_creacion=m.fecha_creacion,
        )

    @staticmethod
    def a_modelo(e: MovimientoStock, m: MovimientoModel | None = None) -> MovimientoModel:
        m = m or MovimientoModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.producto_id = uuid.UUID(str(e.producto_id))
        m.tipo = e.tipo.value
        m.cantidad = e.cantidad
        m.stock_resultante = e.stock_resultante
        m.referencia = e.referencia
        m.usuario_id = uuid.UUID(str(e.usuario_id)) if e.usuario_id else None
        m.lote_id = uuid.UUID(str(e.lote_id)) if e.lote_id else None
        m.observacion = e.observacion
        m.fecha = timezone.make_aware(e.fecha) if timezone.is_naive(e.fecha) else e.fecha
        return m

