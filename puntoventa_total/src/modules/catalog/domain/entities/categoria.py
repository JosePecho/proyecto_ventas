from __future__ import annotations

import re
from dataclasses import dataclass

from src.shared.domain.entities.base_entity import BaseEntity

PATRON_SLUG = re.compile(r"^[a-z0-9-]+$")


@dataclass
class Categoria(BaseEntity):
    nombre: str = ""
    slug: str = ""
    descripcion: str = ""
    orden: int = 0

    def __post_init__(self) -> None:
        self._requerir(self.nombre, "nombre", 80)
        self.slug = self.slug or re.sub(r"[^a-z0-9]+", "-", self.nombre.lower()).strip("-")
        if not PATRON_SLUG.match(self.slug):
            raise ValidationException("Slug invalido (solo minusculas, numeros y guiones)")

    def renombrar(self, nuevo_nombre: str) -> None:
        self._requerir(nuevo_nombre, "nombre", 80)
        self.nombre = nuevo_nombre
        self.marcar_actualizado()

    def mover_a_posicion(self, nueva_posicion: int) -> None:
        if nueva_posicion < 0:
            raise ValidationException("La posicion no puede ser negativa")
        self.orden = nueva_posicion
        self.marcar_actualizado()

from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

