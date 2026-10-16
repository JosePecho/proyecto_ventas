from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="src.modules.orders.tasks.enviar_notificacion_pedido.run", bind=True)
def run(self, pedido_id: str, tipo: str = "listo") -> bool:
    from src.modules.orders.application.use_cases.notificar_pedido_listo import NotificarPedidoListo
    from src.modules.orders.infrastructure.factories import construir_notificador, construir_pedido_repository

    if tipo != "listo":
        logger.info("Tipo de notificacion no soportado aun: %s", tipo)
        return False

    ok = NotificarPedidoListo(construir_pedido_repository(), construir_notificador()).ejecutar(pedido_id)
    logger.info("Notificacion de pedido listo enviada=%s para pedido %s", ok, pedido_id)
    return ok

