from src.modules.promotions.application.ports.frecuencia_cliente_port import FrecuenciaClientePort
from src.modules.promotions.domain.repositories.promocion_repository import PromocionRepository
from src.modules.promotions.infrastructure.adapters.frecuencia_cliente_adapter import FrecuenciaClienteAdapter
from src.modules.promotions.infrastructure.persistence.repositories.django_promocion_repository import (
    DjangoPromocionRepository,
)


def construir_promocion_repository() -> PromocionRepository:
    return DjangoPromocionRepository()


def construir_frecuencia_port() -> FrecuenciaClientePort:
    return FrecuenciaClienteAdapter()

