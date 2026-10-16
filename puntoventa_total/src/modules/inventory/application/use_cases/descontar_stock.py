"""Salida directa (venta en mostrador) con asignacion PEPS."""
from __future__ import annotations

from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.repositories.lote_repository import LoteRepository
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class DescontarStock:
    def __init__(
        self,
        stock_repo: StockRepository,
        lote_repo: LoteRepository,
        mov_repo: MovimientoRepository,
        uow: UnitOfWork | None = None,
    ):
        self._stock = stock_repo
        self._lotes = lote_repo
        self._mov = mov_repo
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, producto_id: str, cantidad: int, referencia: str = "", usuario_id: str = "") -> int:
        with self._uow:
            existencia = self._stock.obtener(producto_id)
            if existencia is None:
                from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente

                raise StockInsuficiente(producto_id, 0, cantidad)

            existencia.aplicar_salida(cantidad)
            lotes = self._lotes.listar_por_producto(producto_id)
            stock_resultante = existencia.cantidad + cantidad
            for lote, tomar in PoliticaStock.planificar_salida_peps(lotes, cantidad):
                lote.descontar(tomar)
                self._lotes.guardar(lote)
                stock_resultante -= tomar
                self._mov.guardar(
                    MovimientoStock(
                        producto_id=producto_id, tipo=TipoMovimiento.SALIDA_VENTA,
                        cantidad=tomar, stock_resultante=stock_resultante,
                        referencia=referencia, usuario_id=usuario_id, lote_id=str(lote.id),
                    )
                )

            self._stock.guardar(existencia)
            return existencia.cantidad

