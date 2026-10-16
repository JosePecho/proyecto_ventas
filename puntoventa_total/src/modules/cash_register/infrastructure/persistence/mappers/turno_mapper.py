import uuid
from decimal import Decimal

from src.modules.cash_register.domain.entities.movimiento_caja import MovimientoCaja
from src.modules.cash_register.domain.entities.turno_caja import TurnoCaja
from src.modules.cash_register.domain.enums.estado_turno import EstadoTurno
from src.modules.cash_register.infrastructure.persistence.django_models.movimiento_caja_model import (
    MovimientoCajaModel,
)
from src.modules.cash_register.infrastructure.persistence.django_models.turno_caja_model import TurnoCajaModel
from src.shared.domain.value_objects.monto import Monto


class TurnoMapper:
    @staticmethod
    def turno_a_dominio(m: TurnoCajaModel) -> TurnoCaja:
        return TurnoCaja(
            id=m.id,
            cajero_id=str(m.cajero_id),
            estado=EstadoTurno(m.estado),
            monto_apertura=Monto(Decimal(m.monto_apertura)),
            monto_cierre=Monto(Decimal(m.monto_cierre)) if m.monto_cierre is not None else None,
            monto_sistema=Monto(Decimal(m.monto_sistema)) if m.monto_sistema is not None else None,
            diferencia=Monto(Decimal(m.diferencia)) if m.diferencia is not None else None,
            fecha_apertura=m.fecha_apertura,
            fecha_cierre=m.fecha_cierre,
            observaciones=m.observaciones,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    @staticmethod
    def turno_a_modelo(e: TurnoCaja, m: TurnoCajaModel | None = None) -> TurnoCajaModel:
        m = m or TurnoCajaModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.cajero_id = uuid.UUID(str(e.cajero_id))
        m.estado = e.estado.value
        m.monto_apertura = e.monto_apertura.valor
        m.monto_cierre = e.monto_cierre.valor if e.monto_cierre else None
        m.monto_sistema = e.monto_sistema.valor if e.monto_sistema else None
        m.diferencia = e.diferencia.valor if e.diferencia else None
        m.fecha_apertura = e.fecha_apertura
        m.fecha_cierre = e.fecha_cierre
        m.observaciones = e.observaciones
        m.activo = e.activo
        return m

    @staticmethod
    def movimiento_a_dominio(m: MovimientoCajaModel) -> MovimientoCaja:
        return MovimientoCaja(
            id=m.id,
            turno_id=str(m.turno_id),
            tipo=m.tipo,
            monto=Monto(Decimal(m.monto)),
            referencia=m.referencia,
            usuario_id=str(m.usuario_id) if m.usuario_id else "",
            observacion=m.observacion,
            fecha_creacion=m.fecha_creacion,
        )

    @staticmethod
    def movimiento_a_modelo(e: MovimientoCaja, m: MovimientoCajaModel | None = None) -> MovimientoCajaModel:
        m = m or MovimientoCajaModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.turno_id = uuid.UUID(str(e.turno_id))
        m.tipo = e.tipo
        m.monto = e.monto.valor
        m.referencia = e.referencia
        m.usuario_id = uuid.UUID(str(e.usuario_id)) if e.usuario_id else None
        m.observacion = e.observacion
        return m

