"""DTOs de salida (vista inmune a cambios internos)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UsuarioOutputDTO:
    id: str
    username: str
    nombre_completo: str
    email: str
    rol: str
    estado: str
    activo: bool
    ultimo_acceso: Optional[str] = None

    @classmethod
    def desde_entidad(cls, usuario) -> "UsuarioOutputDTO":
        return cls(
            id=str(usuario.id),
            username=usuario.username,
            nombre_completo=usuario.nombre_completo,
            email=usuario.email,
            rol=usuario.rol.value,
            estado=usuario.estado.value,
            activo=usuario.activo,
            ultimo_acceso=usuario.ultimo_acceso.isoformat() if usuario.ultimo_acceso else None,
        )

