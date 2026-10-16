"""Adaptador SMS (stub listo para integrar Twilio/Elit)."""
from __future__ import annotations

import logging

from src.modules.orders.application.ports.notificacion_port import NotificacionPort

logger = logging.getLogger(__name__)


class SmsNotifier(NotificacionPort):
    def _enviar(self, telefono: str, mensaje: str) -> bool:
        if not telefono:
            return False
        logger.info("SMS a %s: %s", telefono, mensaje)
        # TODO: integrar proveedor SMS (Twilio, Elit) usando ENCRYPTION_SERVICE
        return True

    def notificar_pedido_confirmado(self, cliente_nombre: str, destino: str, numero: str) -> bool:
        return self._enviar(destino, f"Hola {cliente_nombre}, tu pedido {numero} fue confirmado.")

    def notificar_pedido_listo(self, cliente_nombre: str, destino: str, numero: str) -> bool:
        return self._enviar(destino, f"Hola {cliente_nombre}, tu pedido {numero} esta listo para recojo.")

    def notificar_pedido_cancelado(self, cliente_nombre: str, destino: str, numero: str, motivo: str) -> bool:
        return self._enviar(destino, f"Pedido {numero} cancelado. Motivo: {motivo}")

