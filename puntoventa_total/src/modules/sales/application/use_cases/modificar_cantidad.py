from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.domain.repositories.venta_repository import VentaRepository


class ModificarCantidad:
    def __init__(self, repo: VentaRepository, inventario=None, promociones=None):
        self._repo = repo
        self._inventario = inventario
        self._promociones = promociones

    def ejecutar(self, venta_id: str, producto_id: str, cantidad: int) -> VentaOutputDTO:
        agregado = self._repo.buscar_por_id(venta_id)
        if agregado is None:
            from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

            raise VentaNoEncontrada(venta_id)
        agregado.modificar_cantidad(producto_id, cantidad)
        linea = next(l for l in agregado.lineas if l.producto_id == producto_id)
        if self._inventario is not None and linea.requiere_stock:
            disponible = self._inventario.stock_disponible(producto_id)
            if cantidad > disponible:
                from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
                raise StockInsuficiente(producto_id, disponible, cantidad)
        if self._promociones is not None:
            from src.modules.sales.application.use_cases.agregar_producto import aplicar_beneficio_linea
            aplicar_beneficio_linea(linea, self._promociones)
        agregado.calcular_totales()
        self._repo.guardar(agregado)
        return VentaOutputDTO.desde_agregado(agregado)

