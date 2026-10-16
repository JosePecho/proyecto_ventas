from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ClienteInputDTO:
    nombre: str
    dni: Optional[str] = None
    email: str = ""
    telefono: str = ""
    direccion: str = ""
    usuario_id: Optional[str] = None


@dataclass(frozen=True)
class ActualizarClienteDTO:
    cliente_id: str
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

