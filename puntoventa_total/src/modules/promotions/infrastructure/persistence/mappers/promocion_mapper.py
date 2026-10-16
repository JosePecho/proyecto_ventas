import uuid
from decimal import Decimal

from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.enums.estado_promocion import EstadoPromocion
from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel


class PromocionMapper:
    @staticmethod
    def a_dominio(m: PromocionModel) -> Promocion:
        return Promocion(
            id=m.id,
            nombre=m.nombre,
            tipo=TipoPromocion(m.tipo),
            estado=EstadoPromocion(m.estado),
            producto_id=str(m.producto_id) if m.producto_id else None,
            categoria_id=str(m.categoria_id) if m.categoria_id else None,
            descuento=Descuento(valor=Decimal(m.descuento_valor), tipo=m.tipo, tope=Decimal(m.tope) if m.tope else None),
            cantidad_requerida=m.cantidad_requerida,
            cantidad_gratuita=m.cantidad_gratuita,
            vigencia_desde=m.vigencia_desde,
            vigencia_hasta=m.vigencia_hasta,
            aplica_clientes_frecuentes=m.aplica_clientes_frecuentes,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    @staticmethod
    def a_modelo(e: Promocion, m: PromocionModel | None = None) -> PromocionModel:
        m = m or PromocionModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.nombre = e.nombre
        m.tipo = e.tipo.value
        m.estado = e.estado.value
        m.producto_id = uuid.UUID(str(e.producto_id)) if e.producto_id else None
        m.categoria_id = uuid.UUID(str(e.categoria_id)) if e.categoria_id else None
        m.descuento_valor = e.descuento.valor if e.descuento else 0
        m.tope = e.descuento.tope if e.descuento else None
        m.cantidad_requerida = e.cantidad_requerida
        m.cantidad_gratuita = e.cantidad_gratuita
        m.vigencia_desde = e.vigencia_desde
        m.vigencia_hasta = e.vigencia_hasta
        m.aplica_clientes_frecuentes = e.aplica_clientes_frecuentes
        m.activo = e.activo
        return m

