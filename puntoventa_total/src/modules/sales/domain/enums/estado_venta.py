from enum import Enum


class EstadoVenta(str, Enum):
    BORRADOR = "BORRADOR"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"

    @classmethod
    def opciones(cls):
        return [(e.value, e.value) for e in cls]

