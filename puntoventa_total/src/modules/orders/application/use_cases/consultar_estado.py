from src.modules.orders.application.dto.pedido_output import PedidoOutputDTO
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository


class ConsultarEstado:
    """Uso del cliente (anonimo autenticado por numero de pedido + DNI)."""

    def __init__(self, repo: PedidoRepository):
        self._repo = repo

    def por_numero(self, numero: str) -> PedidoOutputDTO:
        agregado = self._repo.buscar_por_numero(numero)
        if agregado is None:
            from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoNoEncontrado

            raise PedidoNoEncontrado(numero)
        return PedidoOutputDTO.desde_agregado(agregado)

    def del_cliente(self, cliente_id: str) -> list[PedidoOutputDTO]:
        return [PedidoOutputDTO.desde_agregado(a) for a in self._repo.listar_por_cliente(cliente_id)]

    def en_cocina(self) -> list[PedidoOutputDTO]:
        return [
            PedidoOutputDTO.desde_agregado(a)
            for a in self._repo.listar_por_estado("CONFIRMADO") + self._repo.listar_por_estado("EN_PREPARACION")
        ]

