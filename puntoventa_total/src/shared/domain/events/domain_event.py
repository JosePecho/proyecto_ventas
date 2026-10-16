"""Evento de dominio inmutable publicado al ocurrir un hecho relevante."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from src.shared.domain.clock import utc_now


@dataclass(frozen=True)
class DomainEvent:
    evento_id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha: datetime = field(default_factory=utc_now)
    entidad: str = ""

    @property
    def nombre(self) -> str:
        return self.__class__.__name__

    def a_dict(self) -> dict:
        return {
            "evento_id": str(self.evento_id),
            "nombre": self.nombre,
            "entidad": self.entidad,
            "fecha": self.fecha.isoformat(),
            **{k: str(v) for k, v in self.__dict__.items() if not k.startswith("_")},
        }

