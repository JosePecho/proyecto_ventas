"""Ciclo de vida del usuario."""
from enum import Enum


class EstadoUsuario(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    BLOQUEADO = "BLOQUEADO"

    @classmethod
    def opciones(cls):
        return [(estado.value, estado.value) for estado in cls]

