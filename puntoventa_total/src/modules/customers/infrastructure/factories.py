from src.modules.customers.application.ports.historial_compras_port import HistorialComprasPort
from src.modules.customers.domain.repositories.cliente_repository import ClienteRepository
from src.modules.customers.infrastructure.adapters.historial_compras_adapter import HistorialComprasAdapter
from src.modules.customers.infrastructure.persistence.repositories.django_cliente_repository import (
    DjangoClienteRepository,
)


def construir_cliente_repository() -> ClienteRepository:
    return DjangoClienteRepository()


def construir_historial_port() -> HistorialComprasPort:
    return HistorialComprasAdapter()

