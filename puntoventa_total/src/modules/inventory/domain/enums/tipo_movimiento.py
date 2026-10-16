from enum import Enum


class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA_VENTA = "SALIDA_VENTA"
    SALIDA_PEDIDO = "SALIDA_PEDIDO"
    AJUSTE_POSITIVO = "AJUSTE_POSITIVO"
    AJUSTE_NEGATIVO = "AJUSTE_NEGATIVO"
    MERMA = "MERMA"
    DEVOLUCION = "DEVOLUCION"

    @classmethod
    def entradas(cls):
        return {cls.ENTRADA, cls.AJUSTE_POSITIVO, cls.DEVOLUCION}

    @classmethod
    def opciones(cls):
        return [(m.value, m.value) for m in cls]

