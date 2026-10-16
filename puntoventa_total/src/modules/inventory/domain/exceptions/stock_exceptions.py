from src.shared.domain.exceptions.domain_exception import DomainException


class StockException(DomainException):
    codigo = "STOCK_INVALIDO"


class StockInsuficiente(StockException):
    codigo = "STOCK_INSUFICIENTE"

    def __init__(self, producto_id, disponible: int, requerido: int):
        self.disponible = disponible
        self.requerido = requerido
        super().__init__(
            f"Stock insuficiente para el producto {producto_id}: "
            f"disponible {disponible}, requerido {requerido}"
        )


class LoteNoEncontrado(StockException):
    codigo = "LOTE_NO_ENCONTRADO"

    def __init__(self, lote_id):
        super().__init__(f"Lote no encontrado: {lote_id}")


class ReservaNoEncontrada(StockException):
    codigo = "RESERVA_NO_ENCONTRADA"

    def __init__(self, reserva_id):
        super().__init__(f"Reserva no encontrada: {reserva_id}")


class ReservaYaConfirmada(StockException):
    codigo = "RESERVA_YA_CONFIRMADA"

    def __init__(self):
        super().__init__("La reserva ya fue confirmada o liberada")


class ExistenciaNegativa(StockException):
    codigo = "EXISTENCIA_NEGATIVA"

    def __init__(self, producto_id):
        super().__init__(f"La operacion dejaria stock negativo del producto {producto_id}")

