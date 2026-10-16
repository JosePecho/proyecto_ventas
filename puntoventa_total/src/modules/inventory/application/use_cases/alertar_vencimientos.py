from src.modules.inventory.domain.repositories.lote_repository import LoteRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.modules.inventory.application.ports.notificacion_stock_port import NotificacionStockPort


class AlertarVencimientos:
    def __init__(self, repo: LoteRepository, notificador: NotificacionStockPort):
        self._repo = repo
        self._notificador = notificador

    def ejecutar(self) -> int:
        alertados = 0
        for lote in self._repo.lotes_por_vencer(PoliticaStock.dias_alerta_vencimiento()):
            self._notificador.notificar_vencimiento(
                str(lote.id), lote.producto_id, lote.dias_para_vencer or 0
            )
            alertados += 1
        return alertados

