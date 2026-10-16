from enum import Enum


class EstadoPromocion(str, Enum):
    BORRADOR = "BORRADOR"
    PROGRAMADA = "PROGRAMADA"
    ACTIVA = "ACTIVA"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"

    @classmethod
    def opciones(cls):
        return [(e.value, e.value) for e in cls]

