"""Reserva para carrito web/pedido: acota lo disponible sin descontar fisico."""
from __future__ import annotations

from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class ReservarStock:
    def __init__(
        self,
        stock_repo: StockRepository,
        reserva_repo: ReservaRepository,
        uow: UnitOfWork | None = None,
    ):
        self._stock = stock_repo
        self._reservas = reserva_repo
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, producto_id: str, cantidad: int, referencia: str, *, permanente: bool = False) -> str:
        with self._uow:
            existencia = self._stock.obtener(producto_id)
            if existencia is None:
                from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente

                raise StockInsuficiente(producto_id, 0, cantidad)

            existencia.reservar(cantidad)
            reserva = ReservaStock(producto_id=producto_id, cantidad=cantidad, referencia=referencia, permanente=permanente)
            self._stock.guardar(existencia)
            self._reservas.guardar(reserva)
            return str(reserva.id)

