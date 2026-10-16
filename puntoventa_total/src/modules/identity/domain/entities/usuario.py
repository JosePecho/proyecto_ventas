"""Entidad Usuario: identidad autenticable con rol y estado."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.modules.identity.domain.enums.estado_usuario import EstadoUsuario
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.clock import utc_now
from src.shared.domain.exceptions.validation_exception import ValidationException

PATRON_USERNAME = re.compile(r"^[\w.]{4,30}$")
PATRON_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$")


@dataclass
class Usuario(BaseEntity):
    username: str = ""
    password_hash: str = ""
    nombre_completo: str = ""
    email: str = ""
    rol: RolUsuario = RolUsuario.CAJERO
    estado: EstadoUsuario = EstadoUsuario.ACTIVO
    intentos_fallidos: int = 0
    ultimo_acceso: Optional[datetime] = None

    def __post_init__(self) -> None:
        self._requerir(self.username, "username", 30)
        if not PATRON_USERNAME.match(self.username):
            raise ValidationException("Username invalido (4-30 caracteres, sin espacios)")
        self._requerir(self.nombre_completo, "nombre_completo", 120)
        if self.email and not PATRON_EMAIL.match(self.email):
            raise ValidationException("Email invalido")
        if not isinstance(self.rol, RolUsuario):
            self.rol = RolUsuario(self.rol)
        if not isinstance(self.estado, EstadoUsuario):
            self.estado = EstadoUsuario(self.estado)

    MAX_INTENTOS = 5

    def puede_autenticarse(self) -> bool:
        return self.activo and self.estado == EstadoUsuario.ACTIVO

    def registrar_intentofallido(self) -> None:
        """Bloquea al usuario tras varios intentos fallidos."""
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= self.MAX_INTENTOS:
            self.estado = EstadoUsuario.BLOQUEADO
        self.marcar_actualizado()

    def registrar_acceso_exitoso(self) -> None:
        self.intentos_fallidos = 0
        self.ultimo_acceso = utc_now()
        self.marcar_actualizado()

    def cambiar_rol(self, nuevo_rol: RolUsuario) -> None:
        if not isinstance(nuevo_rol, RolUsuario):
            raise ValidationException("Rol invalido")
        self.rol = nuevo_rol
        self.marcar_actualizado()

    def desactivar(self, motivo: str = "") -> None:
        self.estado = EstadoUsuario.INACTIVO
        self.activo = False
        self.marcar_actualizado()

    def cambiar_password(self, password_hash: str) -> None:
        self._requerir(password_hash, "password_hash")
        self.password_hash = password_hash
        self.estado = EstadoUsuario.ACTIVO
        self.activo = True
        self.marcar_actualizado()

    def es_administrador(self) -> bool:
        return self.rol == RolUsuario.ADMINISTRADOR

