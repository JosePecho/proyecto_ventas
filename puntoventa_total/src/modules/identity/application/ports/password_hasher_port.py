"""Puerto de hashing de contrasenas (el modulo no depende de Django aqui)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    @abstractmethod
    def hash(self, clave_plana: str) -> str:
        ...

    @abstractmethod
    def verificar(self, clave_plana: str, clave_hash: str) -> bool:
        ...

