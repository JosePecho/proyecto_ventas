"""Hash de contrasenas con PBKDF2 de Django (adaptador reutilizable)."""
from __future__ import annotations

from django.contrib.auth.hashers import check_password, make_password


class PasswordHasher:
    @staticmethod
    def hash(clave_plana: str) -> str:
        return make_password(clave_plana)

    @staticmethod
    def verificar(clave_plana: str, clave_hash: str) -> bool:
        return check_password(clave_plana, clave_hash)

    @staticmethod
    def necesita_rehash(clave_hash: str) -> bool:
        from django.contrib.auth.hashers import must_update

        return must_update(clave_hash)

