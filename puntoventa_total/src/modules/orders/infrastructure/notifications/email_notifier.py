from django.conf import settings
from django.core.mail import EmailMessage

from src.modules.orders.application.ports.notificacion_port import NotificacionPort


class EmailNotifier(NotificacionPort):
    REMITENTE = "pedidos@puntoventa.local"

    def _enviar(self, destino: str, asunto: str, cuerpo: str) -> bool:
        if not destino:
            return False
        mensaje = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL or self.REMITENTE, [destino])
        return bool(mensaje.send())

    def notificar_pedido_confirmado(self, cliente_nombre: str, destino: str, numero: str) -> bool:
        return self._enviar(
            destino,
            f"Pedido {numero} confirmado",
            f"Hola {cliente_nombre}, tu pedido {numero} fue confirmado y esta en preparacion.",
        )

    def notificar_pedido_listo(self, cliente_nombre: str, destino: str, numero: str) -> bool:
        return self._enviar(
            destino,
            f"Pedido {numero} listo",
            f"Hola {cliente_nombre}, tu pedido {numero} ya puede recogerse.",
        )

    def notificar_pedido_cancelado(self, cliente_nombre: str, destino: str, numero: str, motivo: str) -> bool:
        return self._enviar(
            destino,
            f"Pedido {numero} cancelado",
            f"Hola {cliente_nombre}, tu pedido {numero} fue cancelado. Motivo: {motivo}",
        )

