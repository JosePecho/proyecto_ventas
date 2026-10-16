from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.modules.inventory.application.ports.notificacion_stock_port import NotificacionStockPort


class AlertarStockMinimo:
    def __init__(self, repo: StockRepository, notificador: NotificacionStockPort):
        self._repo = repo
        self._notificador = notificador

    def ejecutar(self) -> int:
        umbral = PoliticaStock.umbral_minimo()
        alertas = self._repo.productos_bajo_minimo()
        for item in alertas:
            self._notificador.notificar_stock_minimo(item["producto_id"], item["disponible"], item.get("stock_minimo", umbral))
        return len(alertas)

