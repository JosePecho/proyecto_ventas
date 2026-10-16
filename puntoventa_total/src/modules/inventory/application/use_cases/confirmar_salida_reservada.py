from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.exceptions.stock_exceptions import ReservaNoEncontrada
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class ConfirmarSalidaReservada:
    def __init__(
        self,
        stock_repo: StockRepository,
        reserva_repo: ReservaRepository,
        mov_repo: MovimientoRepository,
        uow: UnitOfWork | None = None,
    ):
        self._stock = stock_repo
        self._reservas = reserva_repo
        self._mov = mov_repo
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, reserva_id: str, referencia_final: str = "", usuario_id: str = "") -> int:
        with self._uow:
            reserva = self._reservas.buscar_por_id(reserva_id)
            if reserva is None:
                raise ReservaNoEncontrada(reserva_id)

            existencia = self._stock.obtener(reserva.producto_id)
            if existencia is None:
                raise ReservaNoEncontrada(reserva_id)

            existencia.confirmar_reserva(reserva.cantidad)
            reserva.confirmar()

            self._stock.guardar(existencia)
            self._reservas.guardar(reserva)
            self._mov.guardar(
                MovimientoStock(
                    producto_id=reserva.producto_id,
                    tipo=TipoMovimiento.SALIDA_PEDIDO,
                    cantidad=reserva.cantidad,
                    stock_resultante=existencia.cantidad,
                    referencia=referencia_final or reserva.referencia,
                    usuario_id=usuario_id,
                )
            )
            return existencia.cantidad

