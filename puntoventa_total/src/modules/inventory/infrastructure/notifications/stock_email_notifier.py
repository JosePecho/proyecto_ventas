from django.conf import settings
from django.core.mail import send_mail

from src.modules.inventory.application.ports.notificacion_stock_port import NotificacionStockPort


class StockEmailNotifier(NotificacionStockPort):
    DESTINATARIOS_DEFECTO = ["compras@puntoventa.local"]

    def notificar_stock_minimo(self, producto_id: str, stock_actual: int, umbral: int) -> None:
        send_mail(
            subject=f"[Stock minimo] Producto {producto_id}",
            message=f"El producto {producto_id} tiene {stock_actual} unidades (umbral: {umbral}).",
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else "sistema@puntoventa.local",
            recipient_list=self.DESTINATARIOS_DEFECTO,
            fail_silently=True,
        )

    def notificar_vencimiento(self, lote_id: str, producto_id: str, dias_restantes: int) -> None:
        send_mail(
            subject=f"[Vencimiento] Lote {lote_id}",
            message=f"El lote {lote_id} del producto {producto_id} vence en {dias_restantes} dias.",
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else "sistema@puntoventa.local",
            recipient_list=self.DESTINATARIOS_DEFECTO,
            fail_silently=True,
        )

