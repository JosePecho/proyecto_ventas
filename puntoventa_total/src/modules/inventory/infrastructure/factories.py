from src.modules.inventory.application.ports.notificacion_stock_port import NotificacionStockPort
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository
from src.modules.inventory.infrastructure.notifications.stock_email_notifier import StockEmailNotifier
from src.modules.inventory.infrastructure.persistence.repositories.django_lote_repository import (
    DjangoLoteRepository,
)
from src.modules.inventory.infrastructure.persistence.repositories.django_movimiento_repository import (
    DjangoMovimientoRepository,
)
from src.modules.inventory.infrastructure.persistence.repositories.django_reserva_repository import (
    DjangoReservaRepository,
)
from src.modules.inventory.infrastructure.persistence.repositories.django_stock_repository import (
    DjangoStockRepository,
)


def construir_stock_repository() -> DjangoStockRepository:
    return DjangoStockRepository()


def construir_lote_repository() -> DjangoLoteRepository:
    return DjangoLoteRepository()


def construir_reserva_repository() -> ReservaRepository:
    return DjangoReservaRepository()


def construir_movimiento_repository() -> MovimientoRepository:
    return DjangoMovimientoRepository()


def construir_notificador() -> NotificacionStockPort:
    return StockEmailNotifier()

