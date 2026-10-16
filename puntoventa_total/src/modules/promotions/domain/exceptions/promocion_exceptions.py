from src.shared.domain.exceptions.domain_exception import DomainException


class PromocionException(DomainException):
    codigo = "PROMOCION_INVALIDA"


class PromocionNoEncontrada(PromocionException):
    codigo = "PROMOCION_NO_ENCONTRADA"

    def __init__(self, identificador):
        super().__init__(f"Promocion no encontrada: {identificador}")


class PromocionVigenteDuplicada(PromocionException):
    codigo = "PROMOCION_DUPLICADA"

    def __init__(self, producto_id: str):
        super().__init__(f"Ya existe una promocion vigente para el producto {producto_id}")


class VigenciaInvalida(PromocionException):
    codigo = "VIGENCIA_INVALIDA"

    def __init__(self):
        super().__init__("La fecha de fin debe ser posterior a la de inicio")

