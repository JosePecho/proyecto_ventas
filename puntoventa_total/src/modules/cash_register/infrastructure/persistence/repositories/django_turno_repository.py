from typing import Optional, Sequence

from src.modules.cash_register.domain.entities.movimiento_caja import MovimientoCaja
from src.modules.cash_register.domain.entities.turno_caja import TurnoCaja
from src.modules.cash_register.domain.enums.estado_turno import EstadoTurno
from src.modules.cash_register.domain.repositories.turno_repository import TurnoRepository
from src.modules.cash_register.infrastructure.persistence.django_models.movimiento_caja_model import (
    MovimientoCajaModel,
)
from src.modules.cash_register.infrastructure.persistence.django_models.turno_caja_model import TurnoCajaModel
from src.modules.cash_register.infrastructure.persistence.mappers.turno_mapper import TurnoMapper


class DjangoTurnoRepository(TurnoRepository):
    def buscar_por_id(self, turno_id) -> Optional[TurnoCaja]:
        m = TurnoCajaModel.objects.filter(pk=turno_id).first()
        return TurnoMapper.turno_a_dominio(m) if m else None

    def buscar_abierto_por_cajero(self, cajero_id: str) -> Optional[TurnoCaja]:
        m = TurnoCajaModel.objects.filter(cajero_id=cajero_id, estado=EstadoTurno.ABIERTO.value).first()
        return TurnoMapper.turno_a_dominio(m) if m else None

    def guardar(self, turno: TurnoCaja) -> TurnoCaja:
        m = TurnoCajaModel.objects.filter(pk=turno.id).first()
        TurnoMapper.turno_a_modelo(turno, m).save()
        return turno

    def registrar_movimiento(self, movimiento: MovimientoCaja) -> MovimientoCaja:
        m = MovimientoCajaModel.objects.filter(pk=movimiento.id).first()
        TurnoMapper.movimiento_a_modelo(movimiento, m).save()
        return movimiento

    def movimientos_del_turno(self, turno_id: str) -> Sequence[MovimientoCaja]:
        qs = MovimientoCajaModel.objects.filter(turno_id=turno_id).order_by("fecha_creacion")
        return [TurnoMapper.movimiento_a_dominio(m) for m in qs]

    def listar_historico(self, limite: int = 30) -> Sequence[TurnoCaja]:
        return [TurnoMapper.turno_a_dominio(m) for m in TurnoCajaModel.objects.all()[:limite]]

