from django.conf import settings
from django.core.mail import send_mail

from src.modules.orders.application.ports.notificacion_port import NotificacionPort


class EmailNotifier(NotificacionPort):
    REMITENTE = "pedidos@puntoventa.local"

    def _enviar(self, asunto: str, cuerpo: str) -> bool:
        return bool(
            send_mail(asunto, cuerpo, self.REMITENTE, [settings.DEFAULT_FROM_EMAIL or self.REMITENTE], fail_silently=True)
        )

    def notificar_pedido_confirmado(self, cliente_nombre: str, destino: str, numero: str) -> bool:
        return self._enviar(
            f"Pedido {numero} confirmado",
            f"Hola {cliente_nombre}, tu pedido {numero} fue confirmado y esta en preparacion.",
        )

    def notificar_pedido_listo(self, cliente_nombre: str, destino: str, numero: str) -> bool:
        return self._enviar(
            f"Pedido {numero} listo",
            f"Hola {cliente_nombre}, tu pedido {numero} ya puede recogerse.",
        )

    def notificar_pedido_cancelado(self, cliente_nombre: str, destino: str, numero: str, motivo: str) -> bool:
        return self._enviar(
            f"Pedido {numero} cancelado",
            f"Hola {cliente_nombre}, tu pedido {numero} fue cancelado. Motivo: {motivo}",
        )

