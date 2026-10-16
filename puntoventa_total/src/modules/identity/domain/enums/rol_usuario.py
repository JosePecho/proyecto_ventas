"""Roles del sistema."""
from enum import Enum


class RolUsuario(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    GERENTE = "GERENTE"
    CAJERO = "CAJERO"
    ALMACENERO = "ALMACENERO"
    CLIENTE = "CLIENTE"

    @classmethod
    def opciones(cls):
        return [(rol.value, rol.value) for rol in cls]

