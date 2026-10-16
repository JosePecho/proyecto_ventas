from abc import ABC, abstractmethod


class NotificacionPort(ABC):
    @abstractmethod
    def notificar_pedido_confirmado(self, cliente_nombre: str, destino: str, numero: str) -> bool:
        ...

    @abstractmethod
    def notificar_pedido_listo(self, cliente_nombre: str, destino: str, numero: str) -> bool:
        ...

    @abstractmethod
    def notificar_pedido_cancelado(self, cliente_nombre: str, destino: str, numero: str, motivo: str) -> bool:
        ...

