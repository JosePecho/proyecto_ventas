from django.conf import settings
from django.core.mail import send_mail
import logging
from smtplib import SMTPException

from src.modules.inventory.application.ports.notificacion_stock_port import NotificacionStockPort

logger = logging.getLogger(__name__)


def enviar_alerta(**kwargs):
    try:
        send_mail(**kwargs)
    except (SMTPException, OSError):
        # El stock ya se confirmo: informar fallo de entrega sin fingir rollback.
        logger.exception("No se pudo enviar la alerta de inventario")


class StockEmailNotifier(NotificacionStockPort):
    DESTINATARIOS_DEFECTO = ["compras@puntoventa.local"]

    def notificar_stock_minimo(self, producto_id: str, stock_actual: int, umbral: int) -> None:
        enviar_alerta(
            subject=f"[Stock minimo] Producto {producto_id}",
            message=f"El producto {producto_id} tiene {stock_actual} unidades (umbral: {umbral}).",
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else "sistema@puntoventa.local",
            recipient_list=getattr(settings, "STOCK_ALERTA_DESTINATARIOS", self.DESTINATARIOS_DEFECTO),
        )

    def notificar_vencimiento(self, lote_id: str, producto_id: str, dias_restantes: int) -> None:
        enviar_alerta(
            subject=f"[Vencimiento] Lote {lote_id}",
            message=f"El lote {lote_id} del producto {producto_id} vence en {dias_restantes} dias.",
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else "sistema@puntoventa.local",
            recipient_list=getattr(settings, "STOCK_ALERTA_DESTINATARIOS", self.DESTINATARIOS_DEFECTO),
        )

