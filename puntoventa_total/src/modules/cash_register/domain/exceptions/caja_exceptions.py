from src.shared.domain.exceptions.domain_exception import DomainException


class CajaException(DomainException):
    codigo = "CAJA_INVALIDA"


class TurnoYaAbierto(CajaException):
    codigo = "TURNO_YA_ABIERTO"

    def __init__(self, cajero_id: str):
        super().__init__(f"El cajero {cajero_id} ya tiene un turno abierto")


class TurnoNoEncontrado(CajaException):
    codigo = "TURNO_NO_ENCONTRADO"

    def __init__(self, turno_id):
        super().__init__(f"Turno de caja no encontrado: {turno_id}")


class TurnoYaCerrado(CajaException):
    codigo = "TURNO_YA_CERRADO"

    def __init__(self):
        super().__init__("El turno ya fue cerrado")


class MovimientoInvalido(CajaException):
    codigo = "MOVIMIENTO_INVALIDO"

    def __init__(self, mensaje: str):
        super().__init__(mensaje)

