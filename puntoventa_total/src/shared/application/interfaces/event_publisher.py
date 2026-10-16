"""Puerto para publicar eventos de dominio fuera del proceso transaccional."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from src.shared.domain.events.domain_event import DomainEvent


class EventPublisher(ABC):
    @abstractmethod
    def publicar(self, eventos: Iterable[DomainEvent]) -> None:
        """Publica eventos ya confirmados (after commit)."""

