from src.modules.orders.application.dto.pedido_output import PedidoOutputDTO
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository


class PrepararPedido:
    def __init__(self, repo: PedidoRepository):
        self._repo = repo

    def ejecutar(self, pedido_id: str) -> PedidoOutputDTO:
        agregado = self._repo.buscar_por_id(pedido_id)
        if agregado is None:
            from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoNoEncontrado

            raise PedidoNoEncontrado(pedido_id)
        agregado.iniciar_preparacion()
        self._repo.guardar(agregado)
        return PedidoOutputDTO.desde_agregado(agregado)

