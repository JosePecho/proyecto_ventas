from src.modules.inventory.application.dto.stock_dto import StockDTO
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.shared.infrastructure.cache.redis_cache import cache_resultado


class ConsultarStock:
    def __init__(self, repo: StockRepository):
        self._repo = repo

    @cache_resultado(segundos=30, prefijo="inventario:stock")
    def ejecutar(self, producto_id: str) -> StockDTO:
        existencia = self._repo.obtener(producto_id)
        if existencia is None:
            return StockDTO(producto_id=producto_id, cantidad=0, reservada=0, disponible=0, bajo_minimo=True)
        return StockDTO(
            producto_id=producto_id,
            cantidad=existencia.cantidad,
            reservada=existencia.reservada,
            disponible=existencia.disponible,
            bajo_minimo=existencia.con_stock_minimo(PoliticaStock.umbral_minimo()),
        )

