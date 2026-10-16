"""Alta de lote + entrada de existencia + movimiento de kardex (atomico)."""
from __future__ import annotations

from datetime import date

from src.modules.inventory.application.dto.lote_dto import LoteDTO, RecepcionLoteDTO
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.repositories.lote_repository import LoteRepository
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork
from src.shared.domain.value_objects.monto import Monto


class RecibirMercaderia:
    def __init__(
        self,
        stock_repo: StockRepository,
        lote_repo: LoteRepository,
        mov_repo: MovimientoRepository,
        moneda: str = "PEN",
        uow: UnitOfWork | None = None,
    ):
        self._stock = stock_repo
        self._lotes = lote_repo
        self._mov = mov_repo
        self._moneda = moneda
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, datos: RecepcionLoteDTO, usuario_id: str = "") -> LoteDTO:
        with self._uow:
            lote = Lote(
                producto_id=datos.producto_id,
                numero_lote=datos.numero_lote,
                cantidad_inicial=datos.cantidad,
                cantidad_restante=datos.cantidad,
                costo_unitario=Monto(datos.costo_unitario, self._moneda),
                proveedor=datos.proveedor,
                fecha_vencimiento=date.fromisoformat(datos.fecha_vencimiento) if datos.fecha_vencimiento else None,
            )
            existencia = self._stock.obtener(datos.producto_id) or Existencia(producto_id=datos.producto_id)
            stock_anterior = existencia.cantidad
            existencia.aplicar_entrada(datos.cantidad)

            self._lotes.guardar(lote)
            self._stock.guardar(existencia)
            self._mov.guardar(
                MovimientoStock(
                    producto_id=datos.producto_id,
                    tipo=TipoMovimiento.ENTRADA,
                    cantidad=datos.cantidad,
                    stock_resultante=existencia.cantidad,
                    referencia=f"LOTE:{lote.numero_lote}",
                    usuario_id=usuario_id,
                    lote_id=str(lote.id),
                    observacion=f"Ingreso de {datos.cantidad} unidades - {datos.proveedor}",
                )
            )
            lote._stock_anterior = stock_anterior  # contexto para el publicador de eventos
            return LoteDTO.desde_entidad(lote)

