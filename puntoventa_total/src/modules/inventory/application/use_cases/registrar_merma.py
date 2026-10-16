"""Merma: salida justificada que descuenta lote y registra motivo."""
from __future__ import annotations

from datetime import date

from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.enums.motivo_merma import MotivoMerma
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.exceptions.stock_exceptions import LoteNoEncontrado
from src.modules.inventory.domain.repositories.lote_repository import LoteRepository
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class RegistrarMerma:
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

    def ejecutar(
        self,
        producto_id: str,
        cantidad: int,
        motivo: str,
        usuario_id: str,
        lote_id: str | None = None,
        observacion: str = "",
    ) -> int:
        with self._uow:
            try:
                motivo = MotivoMerma(motivo).value
            except ValueError as exc:
                raise ValidationException("Motivo de merma invalido") from exc
            existencia = self._stock.obtener(producto_id)
            if existencia is None:
                raise ValidationException("No hay existencia registrada para este producto")
            if lote_id:
                lote = self._lotes.buscar_por_id(lote_id)
                if lote is None:
                    raise LoteNoEncontrado(lote_id)
                if str(lote.producto_id) != str(producto_id):
                    raise ValidationException("El lote no pertenece al producto")
                if not PoliticaStock.puede_registrar_merma(lote.cantidad_restante, cantidad):
                    raise ValidationException("Cantidad de merma invalida para el lote")
                plan = [(lote, cantidad)]
            else:
                # Las mermas tambien deben consumir lotes vencidos.
                lotes = sorted(
                    self._lotes.listar_por_producto(producto_id),
                    key=lambda lote: (lote.fecha_vencimiento or date.max, lote.fecha_recepcion),
                )
                pendiente = cantidad
                plan = []
                for lote in lotes:
                    tomar = min(lote.cantidad_restante, pendiente)
                    if tomar:
                        plan.append((lote, tomar))
                        pendiente -= tomar
                    if not pendiente:
                        break
                if pendiente:
                    raise ValidationException("Los lotes no cubren la cantidad de merma")
            existencia.aplicar_salida(cantidad)
            for lote, tomar in plan:
                lote.descontar(tomar)
                self._lotes.guardar(lote)
            self._stock.guardar(existencia)

            self._mov.guardar(
                MovimientoStock(
                    producto_id=producto_id,
                    tipo=TipoMovimiento.MERMA,
                    cantidad=cantidad,
                    stock_resultante=existencia.cantidad,
                    referencia=f"MERMA:{motivo}",
                    usuario_id=usuario_id,
                    observacion=observacion,
                    lote_id=lote_id,
                )
            )
            return existencia.cantidad

from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

