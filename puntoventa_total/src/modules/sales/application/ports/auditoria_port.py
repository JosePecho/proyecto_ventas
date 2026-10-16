from abc import ABC, abstractmethod


class AuditoriaPort(ABC):
    @abstractmethod
    def registrar(self, accion: str, entidad: str, entidad_id: str, usuario_id: str, detalle: dict | None = None) -> None:
        ...

