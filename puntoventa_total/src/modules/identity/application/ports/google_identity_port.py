"""Contrato de verificación de identidad externa, independiente de Firebase."""
from abc import ABC, abstractmethod


class GoogleTokenInvalido(Exception):  # noqa: N818 - convención de excepciones del dominio
    pass


class GoogleNoDisponible(Exception):  # noqa: N818 - convención de excepciones del dominio
    pass


class GoogleIdentityPort(ABC):
    @abstractmethod
    def verificar(self, token: str) -> str:
        """Devuelve un correo cuya titularidad está garantizada por Google."""
