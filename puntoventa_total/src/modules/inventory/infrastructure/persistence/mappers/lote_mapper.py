import uuid
from decimal import Decimal

from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.shared.domain.value_objects.monto import Monto


class LoteMapper:
    @staticmethod
    def a_dominio(m: LoteModel) -> Lote:
        return Lote(
            id=m.id,
            producto_id=str(m.producto_id),
            numero_lote=m.numero_lote,
            cantidad_inicial=m.cantidad_inicial,
            cantidad_restante=m.cantidad_restante,
            costo_unitario=Monto(Decimal(m.costo_unitario)) if m.costo_unitario is not None else None,
            proveedor=m.proveedor,
            fecha_vencimiento=m.fecha_vencimiento,
            fecha_recepcion=m.fecha_recepcion,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    @staticmethod
    def a_modelo(e: Lote, m: LoteModel | None = None) -> LoteModel:
        m = m or LoteModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.producto_id = uuid.UUID(str(e.producto_id))
        m.numero_lote = e.numero_lote
        m.cantidad_inicial = e.cantidad_inicial
        m.cantidad_restante = e.cantidad_restante
        m.costo_unitario = e.costo_unitario.valor if e.costo_unitario else None
        m.proveedor = e.proveedor
        m.fecha_vencimiento = e.fecha_vencimiento
        m.fecha_recepcion = e.fecha_recepcion
        m.activo = e.activo
        return m

