"""Tarea Celery: alerta de lotes por vencer."""
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="src.modules.inventory.tasks.verificar_vencimientos.run", bind=True)
def run(self) -> int:
    from src.modules.inventory.application.use_cases.alertar_vencimientos import AlertarVencimientos
    from src.modules.inventory.infrastructure.factories import construir_lote_repository, construir_notificador

    alertas = AlertarVencimientos(construir_lote_repository(), construir_notificador()).ejecutar()
    logger.info("Alertas de vencimiento emitidas: %s", alertas)
    return alertas

