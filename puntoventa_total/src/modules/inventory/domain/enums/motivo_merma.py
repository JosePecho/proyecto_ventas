from enum import Enum


class MotivoMerma(str, Enum):
    VENCIDO = "VENCIDO"
    DANADO = "DANADO"
    ROBO = "ROBO"
    ERROR_INVENTARIO = "ERROR_INVENTARIO"
    OTRO = "OTRO"

    @classmethod
    def opciones(cls):
        return [(m.value, m.value) for m in cls]

