from abc import ABC, abstractmethod

from src.modules.identity.application.dto.google_identity import GoogleIdentity
from src.modules.identity.domain.entities.usuario import Usuario


class GoogleVinculoPort(ABC):
    @abstractmethod
    def buscar_usuario(self, identidad: GoogleIdentity) -> Usuario | None:
        """Resuelve exclusivamente una vinculación previamente autorizada."""
