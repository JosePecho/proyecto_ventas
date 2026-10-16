from src.modules.orders.application.ports.inventario_port import InventarioPort
from src.modules.orders.application.ports.notificacion_port import NotificacionPort
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository
from src.modules.orders.infrastructure.adapters.inventario_adapter import InventarioAdapter
from src.modules.orders.infrastructure.notifications.sms_notifier import SmsNotifier
from src.modules.orders.infrastructure.persistence.repositories.django_pedido_repository import (
    DjangoPedidoRepository,
)


def construir_pedido_repository() -> PedidoRepository:
    return DjangoPedidoRepository()


def construir_inventario_port() -> InventarioPort:
    return InventarioAdapter()


def construir_notificador() -> NotificacionPort:
    return SmsNotifier()


def construir_reserva_repository():
    from src.modules.inventory.infrastructure.factories import construir_reserva_repository as _c

    return _c()

