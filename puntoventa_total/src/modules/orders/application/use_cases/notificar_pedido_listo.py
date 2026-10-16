from src.modules.orders.application.ports.notificacion_port import NotificacionPort
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository


class NotificarPedidoListo:
    def __init__(self, repo: PedidoRepository, notificador: NotificacionPort):
        self._repo = repo
        self._notificador = notificador

    def ejecutar(self, pedido_id: str) -> bool:
        agregado = self._repo.buscar_por_id(pedido_id)
        if agregado is None:
            return False
        p = agregado.pedido
        destino = p.cliente_telefono or ""
        return self._notificador.notificar_pedido_listo(p.cliente_nombre, destino, p.numero)

