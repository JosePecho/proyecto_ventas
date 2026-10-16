from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ClienteOutputDTO:
    id: str
    nombre: str
    dni: Optional[str]
    email: str
    telefono: str
    direccion: str
    puntos_fidelidad: int
    activo: bool

    @classmethod
    def desde_entidad(cls, c) -> "ClienteOutputDTO":
        return cls(
            id=str(c.id),
            nombre=c.nombre,
            dni=str(c.dni) if c.dni else None,
            email=c.email,
            telefono=c.telefono,
            direccion=c.direccion,
            puntos_fidelidad=c.puntos_fidelidad,
            activo=c.activo,
        )

