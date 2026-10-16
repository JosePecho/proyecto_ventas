from abc import ABC, abstractmethod


class NotificacionStockPort(ABC):
    @abstractmethod
    def notificar_stock_minimo(self, producto_id: str, stock_actual: int, umbral: int) -> None:
        ...

    @abstractmethod
    def notificar_vencimiento(self, lote_id: str, producto_id: str, dias_restantes: int) -> None:
        ...

