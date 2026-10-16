"""Adaptador que cumple el puerto PasswordHasherPort usando Django/crypto."""
from __future__ import annotations

from src.modules.identity.application.ports.password_hasher_port import PasswordHasherPort
from src.shared.infrastructure.security.password_hasher import PasswordHasher


class DjangoAuthAdapter(PasswordHasherPort):
    def hash(self, clave_plana: str) -> str:
        return PasswordHasher.hash(clave_plana)

    def verificar(self, clave_plana: str, clave_hash: str) -> bool:
        return PasswordHasher.verificar(clave_plana, clave_hash)

