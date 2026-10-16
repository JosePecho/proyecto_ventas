from src.modules.orders.application.dto.pedido_input import CrearPedidoDTO
from src.modules.orders.application.dto.pedido_output import PedidoOutputDTO
from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository


class CrearPedido:
    def __init__(self, repo: PedidoRepository):
        self._repo = repo

    def ejecutar(self, datos: CrearPedidoDTO) -> PedidoOutputDTO:
        pedido = Pedido(
            numero=self._repo.siguiente_numero(),
            cliente_id=datos.cliente_id,
            cliente_nombre=datos.cliente_nombre,
            cliente_dni=datos.cliente_dni,
            cliente_telefono=datos.cliente_telefono,
            observaciones=datos.observaciones,
            moneda=datos.moneda,
        )
        agregado = PedidoAggregate(pedido=pedido)
        self._repo.guardar(agregado)
        return PedidoOutputDTO.desde_agregado(agregado)

