from enum import Enum


class EstadoPedido(str, Enum):
    BORRADOR = "BORRADOR"
    CONFIRMADO = "CONFIRMADO"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO = "LISTO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"

    @classmethod
    def opciones(cls):
        return [(e.value, e.value) for e in cls]

    def puede_transicion_a(self, siguiente: "EstadoPedido") -> bool:
        flujo = {
            EstadoPedido.BORRADOR: {EstadoPedido.CONFIRMADO, EstadoPedido.CANCELADO},
            EstadoPedido.CONFIRMADO: {EstadoPedido.EN_PREPARACION, EstadoPedido.CANCELADO},
            EstadoPedido.EN_PREPARACION: {EstadoPedido.LISTO, EstadoPedido.CANCELADO},
            EstadoPedido.LISTO: {EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO},
            EstadoPedido.ENTREGADO: set(),
            EstadoPedido.CANCELADO: set(),
        }
        return siguiente in flujo.get(self, set())

