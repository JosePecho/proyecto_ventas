"""Entidad Cliente con datos de contacto validados."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.dni import DNI

PATRON_TEL = re.compile(r"^\+?9?\d{7,12}$")
PATRON_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")


@dataclass
class Cliente(BaseEntity):
    nombre: str = ""
    dni: Optional[DNI] = None
    email: str = ""
    telefono: str = ""
    direccion: str = ""
    usuario_id: Optional[str] = None
    puntos_fidelidad: int = 0

    def __post_init__(self) -> None:
        self._requerir(self.nombre, "nombre", 120)
        if self.email and not PATRON_EMAIL.match(self.email):
            raise ValidationException("Email invalido")
        if self.telefono and not PATRON_TEL.match(self.telefono):
            raise ValidationException("Telefono invalido")
        if self.dni and not isinstance(self.dni, DNI):
            self.dni = DNI(self.dni)
        if self.puntos_fidelidad < 0:
            raise ValidationException("Los puntos no pueden ser negativos")

    def actualizar_contacto(self, email: str = "", telefono: str = "", direccion: str = "") -> None:
        if email and not PATRON_EMAIL.match(email):
            raise ValidationException("Email invalido")
        if telefono and not PATRON_TEL.match(telefono):
            raise ValidationException("Telefono invalido")
        self.email = email or self.email
        self.telefono = telefono or self.telefono
        self.direccion = direccion or self.direccion
        self.marcar_actualizado()

    def acumular_puntos(self, puntos: int) -> None:
        if puntos > 0:
            self.puntos_fidelidad += puntos
            self.marcar_actualizado()

    def canjear_puntos(self, puntos: int) -> None:
        if puntos <= 0 or puntos > self.puntos_fidelidad:
            raise ValidationException("Puntos insuficientes para canjear")
        self.puntos_fidelidad -= puntos
        self.marcar_actualizado()

    def anonimizar(self) -> None:
        """Derecho al olvido: conserva solo trazabilidad de ventas."""
        self.nombre = "CLIENTE ELIMINADO"
        self.email = ""
        self.telefono = ""
        self.direccion = ""
        self.dni = None
        self.desactivar()

