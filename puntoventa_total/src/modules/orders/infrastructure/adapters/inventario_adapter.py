from django.db import transaction

from src.modules.inventory.application.use_cases.confirmar_salida_reservada import ConfirmarSalidaReservada
from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
from src.modules.inventory.application.use_cases.reservar_stock import ReservarStock
from src.modules.inventory.infrastructure.factories import (
    construir_lote_repository,
    construir_movimiento_repository,
    construir_reserva_repository,
    construir_stock_repository,
)
from src.modules.orders.application.ports.inventario_port import InventarioPort


class InventarioAdapter(InventarioPort):
    def reservar(self, producto_id: str, cantidad: int, referencia: str) -> str:
        return ReservarStock(
            construir_stock_repository(), construir_reserva_repository(), uow=transaction.atomic()
        ).ejecutar(
            producto_id, cantidad, referencia, permanente=True
        )

    def confirmar_reserva(self, reserva_id: str, referencia: str, usuario_id: str = "") -> int:
        return ConfirmarSalidaReservada(
            construir_stock_repository(),
            construir_reserva_repository(),
            construir_movimiento_repository(),
            uow=transaction.atomic(),
            lote_repo=construir_lote_repository(),
        ).ejecutar(reserva_id, referencia, usuario_id)

    def liberar(self, reserva_id: str) -> None:
        LiberarReserva(
            construir_stock_repository(), construir_reserva_repository(), uow=transaction.atomic()
        ).ejecutar(reserva_id)

    def stock_disponible(self, producto_id: str) -> int:
        return ConsultarStock(construir_stock_repository()).ejecutar(producto_id).disponible

    def devolver(self, producto_id: str, cantidad: int, referencia: str, usuario_id: str = "") -> int:
        from src.modules.inventory.domain.entities.existencia import Existencia
        from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
        from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento

        repo_stock = construir_stock_repository()
        existencia = repo_stock.obtener(producto_id) or Existencia(producto_id=producto_id)
        existencia.aplicar_entrada(cantidad)
        repo_stock.guardar(existencia)
        construir_movimiento_repository().guardar(
            MovimientoStock(
                producto_id=producto_id,
                tipo=TipoMovimiento.DEVOLUCION,
                cantidad=cantidad,
                stock_resultante=existencia.cantidad,
                referencia=referencia,
                usuario_id=usuario_id,
            )
        )
        return existencia.cantidad

