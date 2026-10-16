from enum import Enum


class MotivoMerma(str, Enum):
    VENCIDO = "VENCIDO"
    DANADO = "DANADO"
    ROBO = "ROBO"
    ERROR_INVENTARIO = "ERROR_INVENTARIO"
    OTRO = "OTRO"

    @classmethod
    def opciones(cls):
        etiquetas = {"VENCIDO": "Vencimiento", "DANADO": "Daño", "ROBO": "Robo",
                     "ERROR_INVENTARIO": "Error de inventario", "OTRO": "Otro"}
        return [(m.value, etiquetas[m.value]) for m in cls]

