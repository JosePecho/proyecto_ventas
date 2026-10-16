from enum import Enum


class EstadoProducto(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    DESCONTINUADO = "DESCONTINUADO"

    @classmethod
    def opciones(cls):
        return [(e.value, e.value) for e in cls]

