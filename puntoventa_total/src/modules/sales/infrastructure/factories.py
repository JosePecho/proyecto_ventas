from src.modules.sales.application.ports.auditoria_port import AuditoriaPort
from src.modules.sales.application.ports.inventario_port import InventarioPort
from src.modules.sales.application.ports.promociones_port import PromocionesPort
from src.modules.sales.application.ports.ticket_port import TicketPort
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.modules.sales.infrastructure.adapters.inventario_adapter import InventarioAdapter
from src.modules.sales.infrastructure.adapters.promociones_adapter import PromocionesAdapter
from src.modules.sales.infrastructure.auditing.auditoria_adapter import AuditoriaAdapter
from src.modules.sales.infrastructure.external_services.ticket_printer import TicketPrinter
from src.modules.sales.infrastructure.persistence.repositories.django_venta_repository import (
    DjangoVentaRepository,
)


def construir_venta_repository() -> VentaRepository:
    return DjangoVentaRepository()


def construir_inventario_port() -> InventarioPort:
    return InventarioAdapter()


def construir_promociones_port() -> PromocionesPort:
    return PromocionesAdapter()


def construir_ticket_port() -> TicketPort:
    return TicketPrinter()


def construir_auditoria_port() -> AuditoriaPort:
    return AuditoriaAdapter()

