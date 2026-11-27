"""Contrato de verificación de identidad externa, independiente de Firebase."""
from abc import ABC, abstractmethod

from src.modules.identity.application.dto.google_identity import GoogleIdentity


class GoogleTokenInvalido(Exception):  # noqa: N818 - convención de excepciones del dominio
    pass


class GoogleNoDisponible(Exception):  # noqa: N818 - convención de excepciones del dominio
    pass


class GoogleIdentityPort(ABC):
    @abstractmethod
    def verificar(self, token: str) -> GoogleIdentity:
        """Devuelve la identidad cuya titularidad está garantizada por Google."""
