from dataclasses import dataclass


@dataclass(frozen=True)
class ClienteInputDTO:
    nombre: str
    dni: str | None = None
    email: str = ""
    telefono: str = ""
    direccion: str = ""
    usuario_id: str | None = None


@dataclass(frozen=True)
class ActualizarClienteDTO:
    cliente_id: str
    nombre: str | None = None
    email: str | None = None
    telefono: str | None = None
    direccion: str | None = None

