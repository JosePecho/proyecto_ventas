"""Ajuste por inventario fisico (diferencia positiva/negativa)."""
from __future__ import annotations

from src.modules.inventory.application.dto.stock_dto import AjusteStockDTO
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class AjustarStock:
    def __init__(
        self,
        stock_repo: StockRepository,
        mov_repo: MovimientoRepository,
        uow: UnitOfWork | None = None,
    ):
        self._stock = stock_repo
        self._mov = mov_repo
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, datos: AjusteStockDTO) -> int:
        if datos.cantidad == 0:
            raise ValidationException("El ajuste debe indicar una diferencia distinta de cero")

        with self._uow:
            existencia = self._stock.obtener(datos.producto_id) or Existencia(producto_id=datos.producto_id)
            positivo = datos.cantidad > 0

            if positivo:
                existencia.aplicar_entrada(datos.cantidad)
            else:
                existencia.aplicar_salida(abs(datos.cantidad))

            if not positivo and existencia.reservada > existencia.cantidad:
                raise ExistenciaNegativa(datos.producto_id)

            self._stock.guardar(existencia)
            self._mov.guardar(
                MovimientoStock(
                    producto_id=datos.producto_id,
                    tipo=TipoMovimiento.AJUSTE_POSITIVO if positivo else TipoMovimiento.AJUSTE_NEGATIVO,
                    cantidad=abs(datos.cantidad),
                    stock_resultante=existencia.cantidad,
                    referencia="AJUSTE",
                    usuario_id=datos.usuario_id,
                    observacion=datos.observacion,
                )
            )
            return existencia.cantidad

from src.modules.inventory.domain.exceptions.stock_exceptions import ExistenciaNegativa  # noqa: E402
from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

