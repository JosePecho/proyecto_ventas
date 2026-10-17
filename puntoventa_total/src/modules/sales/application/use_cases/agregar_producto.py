"""Agrega producto al carrito verificando catalogo e inventario."""
from __future__ import annotations

from decimal import Decimal

from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.application.ports.inventario_port import InventarioPort
from src.modules.sales.application.ports.promociones_port import PromocionesPort
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto


class AgregarProducto:
    def __init__(self, repo: VentaRepository, inventario: InventarioPort, promociones: PromocionesPort):
        self._repo = repo
        self._inventario = inventario
        self._promociones = promociones

    def ejecutar(self, venta_id: str, producto, cantidad: int = 1) -> VentaOutputDTO:
        from src.modules.catalog.domain.entities.producto import Producto

        if not isinstance(producto, Producto):
            raise ValidationException("Producto invalido")
        producto.verificar_disponibilidad_venta()

        if producto.requiere_stock:
            disponible = self._inventario.stock_disponible(str(producto.id))
            if disponible < cantidad:
                from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente

                raise StockInsuficiente(str(producto.id), disponible, cantidad)

        agregado = self._repo.buscar_por_id(venta_id)
        if agregado is None:
            from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

            raise VentaNoEncontrada(venta_id)

        agregar_linea(agregado, producto, cantidad, self._promociones)
        # calcular ANTES de guardar: si se persiste primero, la venta queda en
        # la BD con totales obsoletos (total=0) y ProcesarPago cerraria la venta
        # con cualquier pago parcial.
        agregado.calcular_totales()
        self._repo.guardar(agregado)
        return VentaOutputDTO.desde_agregado(agregado)


def agregar_linea(agregado, producto, cantidad: int, promociones) -> None:
    linea = agregado.agregar_producto(
        str(producto.id), producto.nombre, cantidad, producto.precio.venta
    )
    linea.costo_unitario = producto.precio.costo
    descuento = promociones.descuento_producto(str(producto.id), linea.subtotal, cantidad)
    if descuento.valor > 0:
        pct = (descuento.valor / linea.subtotal.valor * Decimal("100")).quantize(Decimal("0.01"))
        linea.aplicar_descuento_pct(pct)

