from src.modules.orders.application.dto.pedido_output import PedidoOutputDTO
from src.modules.orders.application.ports.inventario_port import InventarioPort
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository


class AgregarProductoPedido:
    def __init__(self, repo: PedidoRepository, inventario: InventarioPort):
        self._repo = repo
        self._inventario = inventario

    def ejecutar(self, pedido_id: str, producto, cantidad: int = 1) -> PedidoOutputDTO:
        from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise PedidoException("La cantidad debe ser un entero mayor a cero")
        producto.verificar_disponibilidad_venta()
        agregado = self._repo.buscar_por_id(pedido_id)
        if agregado is None:
            from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoNoEncontrado
            raise PedidoNoEncontrado(pedido_id)
        acumulada = cantidad + sum(l.cantidad for l in agregado.lineas if l.producto_id == str(producto.id))
        if producto.requiere_stock:
            disponible = self._inventario.stock_disponible(str(producto.id))
            if disponible < acumulada:
                from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente

                raise StockInsuficiente(str(producto.id), disponible, acumulada)

        agregado.agregar_producto(str(producto.id), producto.nombre, cantidad, producto.precio.venta, producto.requiere_stock)
        self._repo.guardar(agregado)
        return PedidoOutputDTO.desde_agregado(agregado)

