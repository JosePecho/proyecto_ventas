"""Tarea beat: activa programadas iniciadas y finaliza vencidas."""
from __future__ import annotations

import logging

from celery import shared_task
from src.modules.auditing.infrastructure.request_audit import auditar_tarea

logger = logging.getLogger(__name__)


@shared_task(name="src.modules.promotions.tasks.actualizar_estado_promociones.run", bind=True)
@auditar_tarea
def run(self) -> dict:
    from django.utils import timezone

    from src.modules.promotions.domain.enums.estado_promocion import EstadoPromocion
    from src.modules.promotions.infrastructure.factories import construir_promocion_repository

    repo = construir_promocion_repository()
    ahora = timezone.now()
    activadas = finalizadas = 0

    for promocion in repo.listar():
        if promocion.estado in (EstadoPromocion.PROGRAMADA, EstadoPromocion.ACTIVA) and promocion.vigencia_hasta and promocion.vigencia_hasta <= ahora:
            promocion.finalizar()
            repo.guardar(promocion)
            finalizadas += 1
        elif promocion.estado == EstadoPromocion.PROGRAMADA and promocion.vigencia_desde and promocion.vigencia_desde <= ahora:
            promocion.activar()
            repo.guardar(promocion)
            activadas += 1
        elif promocion.estado == EstadoPromocion.ACTIVA and promocion.vigencia_hasta and promocion.vigencia_hasta < ahora:
            promocion.finalizar()
            repo.guardar(promocion)
            finalizadas += 1

    logger.info("Promociones activadas=%s finalizadas=%s", activadas, finalizadas)
    return {"activadas": activadas, "finalizadas": finalizadas}

