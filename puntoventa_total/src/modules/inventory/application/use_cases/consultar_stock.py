from src.modules.inventory.application.dto.stock_dto import StockDTO
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock


class ConsultarStock:
    def __init__(self, repo: StockRepository):
        self._repo = repo

    def ejecutar(self, producto_id: str) -> StockDTO:
        existencia = self._repo.obtener(producto_id)
        if existencia is None:
            return StockDTO(producto_id=producto_id, cantidad=0, reservada=0, disponible=0,
                            bajo_minimo=self._repo.umbral_minimo(producto_id, PoliticaStock.umbral_minimo()) > 0)
        return StockDTO(
            producto_id=producto_id,
            cantidad=existencia.cantidad,
            reservada=existencia.reservada,
            disponible=existencia.disponible,
            bajo_minimo=existencia.disponible < self._repo.umbral_minimo(producto_id, PoliticaStock.umbral_minimo()),
        )

