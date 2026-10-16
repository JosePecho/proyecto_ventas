from src.shared.domain.exceptions.domain_exception import DomainException


class PedidoException(DomainException):
    codigo = "PEDIDO_INVALIDO"


class PedidoNoEncontrado(PedidoException):
    codigo = "PEDIDO_NO_ENCONTRADO"

    def __init__(self, pedido_id):
        super().__init__(f"Pedido no encontrado: {pedido_id}")


class TransicionInvalida(PedidoException):
    codigo = "TRANSICION_INVALIDA"

    def __init__(self, actual: str, siguiente: str):
        super().__init__(f"No se puede pasar de {actual} a {siguiente}")


class PedidoCancelado(PedidoException):
    codigo = "PEDIDO_CANCELADO"

    def __init__(self):
        super().__init__("El pedido fue cancelado")


class HoraRecojoInvalida(PedidoException):
    codigo = "HORA_RECOJO_INVALIDA"

    def __init__(self, detalle: str = ""):
        super().__init__(f"La hora de recojo no es valida: {detalle}")

