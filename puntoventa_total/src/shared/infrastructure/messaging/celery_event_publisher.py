"""Publicacion diferida de eventos de dominio via Celery."""
from __future__ import annotations

from typing import Iterable

from celery import shared_task

from src.shared.domain.events.domain_event import DomainEvent


@shared_task(name="shared.publicar_evento_dominio")
def publicar_evento_dominio(payload: dict) -> None:
    """Consumidor generico: deja traza del evento en log.

    Los modulos registran sus propios consumidores con `bind=True`.
    """
    import logging

    logging.getLogger("eventos").info("Evento de dominio recibido: %s", payload)


class CeleryEventPublisher:
    """Implementa el puerto `EventPublisher` usando la cola de Celery."""

    def publicar(self, eventos: Iterable[DomainEvent]) -> None:
        for evento in eventos:
            publicar_evento_dominio.delay(evento.a_dict())

