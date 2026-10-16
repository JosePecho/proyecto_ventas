from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, Sequence

from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria


class AuditoriaRepository(ABC):
    @abstractmethod
    def guardar(self, registro: RegistroAuditoria) -> RegistroAuditoria:
        ...

    @abstractmethod
    def buscar_por_id(self, registro_id) -> Optional[RegistroAuditoria]:
        ...

    @abstractmethod
    def consultar(
        self,
        accion: str | None = None,
        entidad: str | None = None,
        entidad_id: str | None = None,
        usuario_id: str | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        limite: int = 100,
    ) -> Sequence[RegistroAuditoria]:
        ...

    @abstractmethod
    def trazas_de_entidad(self, entidad: str, entidad_id: str) -> Sequence[RegistroAuditoria]:
        """Historial completo de una transaccion/entidad (rastreo)."""
        ...

