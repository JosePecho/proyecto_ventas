"""DTOs de entrada del modulo identidad."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.modules.identity.domain.enums.rol_usuario import RolUsuario


@dataclass(frozen=True)
class UsuarioInputDTO:
    username: str
    password: str
    nombre_completo: str
    email: str = ""
    rol: str = RolUsuario.CAJERO.value


@dataclass(frozen=True)
class ActualizarUsuarioDTO:
    usuario_id: str
    nombre_completo: str = ""
    email: str = ""
    password_nueva: Optional[str] = None
    rol: Optional[str] = None

