"""Cifrado simetrico de datos sensibles (tarjetas tokenizadas, telefonos)."""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class EncryptionService:
    """Clave derivada del SECRET_KEY; sin criptografia propia por modulo."""

    def __init__(self, clave: bytes | None = None):
        if clave is None:
            secreto = getattr(settings, "SECRET_KEY", "dev").encode()
            clave = base64.urlsafe_b64encode(hashlib.sha256(secreto).digest())
        self._fernet = Fernet(clave)

    def cifrar(self, texto_plano: str) -> str:
        return self._fernet.encrypt(texto_plano.encode()).decode()

    def descifrar(self, texto_cifrado: str) -> str:
        try:
            return self._fernet.decrypt(texto_cifrado.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("Token invalido o clave incorrecta") from exc
