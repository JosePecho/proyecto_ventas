from src.modules.cash_register.application.ports.ventas_turno_port import VentasTurnoPort
from src.modules.cash_register.domain.repositories.turno_repository import TurnoRepository
from src.modules.cash_register.infrastructure.adapters.ventas_turno_adapter import VentasTurnoAdapter
from src.modules.cash_register.infrastructure.persistence.repositories.django_turno_repository import (
    DjangoTurnoRepository,
)


def construir_turno_repository() -> TurnoRepository:
    return DjangoTurnoRepository()


def construir_ventas_turno_port() -> VentasTurnoPort:
    return VentasTurnoAdapter()

