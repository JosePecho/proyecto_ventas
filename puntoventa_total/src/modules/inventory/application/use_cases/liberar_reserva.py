from src.modules.inventory.domain.exceptions.stock_exceptions import (
    ReservaNoEncontrada,
    ReservaYaConfirmada,
)
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class LiberarReserva:
    def __init__(
        self,
        stock_repo: StockRepository,
        reserva_repo: ReservaRepository,
        uow: UnitOfWork | None = None,
    ):
        self._stock = stock_repo
        self._reservas = reserva_repo
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, reserva_id: str) -> None:
        with self._uow:
            reserva = self._reservas.buscar_por_id(reserva_id)
            if reserva is None:
                raise ReservaNoEncontrada(reserva_id)
            if reserva.confirmada:
                raise ReservaYaConfirmada()

            existencia = self._stock.obtener(reserva.producto_id)
            if existencia:
                existencia.liberar(reserva.cantidad)
                self._stock.guardar(existencia)

            reserva.liberar()
            self._reservas.guardar(reserva)

    def liberar_expiradas(self) -> int:
        """Liberacion masiva (tarea programada)."""
        liberadas = 0
        for reserva in self._reservas.listar_activas_expiradas():
            self.ejecutar(str(reserva.id))
            liberadas += 1
        return liberadas

