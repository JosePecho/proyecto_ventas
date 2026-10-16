from enum import Enum


class TipoPromocion(str, Enum):
    PORCENTAJE = "PORCENTAJE"
    MONTO_FIJO = "MONTO_FIJO"
    NX1 = "NX1"          # 2x1, 3x2, etc.
    PRECIO_ESPECIAL = "PRECIO_ESPECIAL"

    @classmethod
    def opciones(cls):
        return [(t.value, t.value) for t in cls]

