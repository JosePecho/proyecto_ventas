from src.modules.catalog.application.ports.disponibilidad_port import DisponibilidadPort
from src.modules.catalog.domain.repositories.categoria_repository import CategoriaRepository
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.modules.catalog.infrastructure.adapters.disponibilidad_adapter import DisponibilidadAdapter
from src.modules.catalog.infrastructure.persistence.repositories.django_categoria_repository import (
    DjangoCategoriaRepository,
)
from src.modules.catalog.infrastructure.persistence.repositories.django_producto_repository import (
    DjangoProductoRepository,
)


def construir_producto_repository() -> ProductoRepository:
    return DjangoProductoRepository()


def construir_categoria_repository() -> CategoriaRepository:
    return DjangoCategoriaRepository()


def construir_disponibilidad_port() -> DisponibilidadPort:
    return DisponibilidadAdapter()

