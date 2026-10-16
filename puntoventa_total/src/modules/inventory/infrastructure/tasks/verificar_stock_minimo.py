"""Tarea Celery: alerta de productos por debajo del umbral."""
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="src.modules.inventory.tasks.verificar_stock_minimo.run", bind=True)
def run(self) -> int:
    from src.modules.inventory.application.use_cases.alertar_stock_minimo import AlertarStockMinimo
    from src.modules.inventory.infrastructure.factories import construir_notificador, construir_stock_repository

    alertas = AlertarStockMinimo(construir_stock_repository(), construir_notificador()).ejecutar()
    logger.info("Alertas de stock minimo emitidas: %s", alertas)
    return alertas

