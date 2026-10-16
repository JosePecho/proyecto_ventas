"""Entidad base: identidad temporal, trazabilidad y recoleccion de eventos de dominio."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.shared.domain.events.domain_event import DomainEvent
from src.shared.domain.clock import utc_now
from src.shared.domain.exceptions.validation_exception import ValidationException


@dataclass
class BaseEntity:
    """Base de todas las entidades de dominio.

    Las entidades se construyen ya validadas: cualquier regla invariante
    debe ejecutarse en `__post_init__` y lanzar `ValidationException`.
    """

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha_creacion: datetime = field(default_factory=utc_now)
    fecha_actualizacion: datetime = field(default_factory=utc_now)
    activo: bool = True
    _eventos: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def _validar(self, condicion: bool, mensaje: str) -> None:
        if not condicion:
            raise ValidationException(mensaje)

    def _requerir(self, valor: Any, nombre: str, max_len: int | None = None) -> None:
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            raise ValidationException(f"El campo '{nombre}' es obligatorio")
        if max_len and isinstance(valor, str) and len(valor) > max_len:
            raise ValidationException(f"El campo '{nombre}' supera {max_len} caracteres")

    def marcar_actualizado(self) -> None:
        self.fecha_actualizacion = utc_now()

    def desactivar(self) -> None:
        self.activo = False
        self.marcar_actualizado()

    def activar(self) -> None:
        self.activo = True
        self.marcar_actualizado()

    # --- Eventos de dominio ---
    def _publicar(self, evento: DomainEvent) -> None:
        self._eventos.append(evento)

    def eventos_pendientes(self) -> list[DomainEvent]:
        return list(self._eventos)

    def limpiar_eventos(self) -> None:
        self._eventos.clear()

