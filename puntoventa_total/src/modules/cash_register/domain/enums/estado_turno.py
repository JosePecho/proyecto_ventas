from enum import Enum


class EstadoTurno(str, Enum):
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"

    @classmethod
    def opciones(cls):
        return [(e.value, e.value) for e in cls]

