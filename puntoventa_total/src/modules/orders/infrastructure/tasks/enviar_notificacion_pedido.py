from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="src.modules.orders.tasks.enviar_notificacion_pedido.run", bind=True,
             autoretry_for=(OSError,), retry_backoff=True, max_retries=5)
def run(self, pedido_id: str, tipo: str = "listo") -> bool:
    from src.modules.orders.application.use_cases.notificar_pedido_listo import NotificarPedidoListo
    from src.modules.orders.infrastructure.factories import construir_notificador, construir_pedido_repository

    if tipo != "listo":
        logger.info("Tipo de notificacion no soportado aun: %s", tipo)
        return False

    from django.db import transaction
    from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
    with transaction.atomic():
        pedido = PedidoModel.objects.select_for_update().filter(pk=pedido_id).first()
        if pedido is None or pedido.estado != "LISTO":
            return False
        if pedido.notificado_listo:
            return True
        ok = NotificarPedidoListo(construir_pedido_repository(), construir_notificador()).ejecutar(pedido_id)
        if ok:
            pedido.notificado_listo = True
            pedido.save(update_fields=["notificado_listo"])
    logger.info("Notificacion de pedido listo enviada=%s para pedido %s", ok, pedido_id)
    return ok


@shared_task(name="src.modules.orders.tasks.reintentar_notificaciones")
def reintentar_pendientes():
    from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
    ids = PedidoModel.objects.filter(estado="LISTO", notificado_listo=False).values_list("id", flat=True)
    for pedido_id in ids.iterator():
        run.delay(str(pedido_id))

