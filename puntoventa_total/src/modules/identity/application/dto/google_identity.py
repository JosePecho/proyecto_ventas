"""Datos mínimos verificados; nunca incluye tokens."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleIdentity:
    uid: str
    email: str
    nombre: str
    proyecto: str
    auth_time: int
