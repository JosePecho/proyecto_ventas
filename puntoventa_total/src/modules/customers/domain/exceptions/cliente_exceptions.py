from src.shared.domain.exceptions.domain_exception import DomainException


class ClienteException(DomainException):
    codigo = "CLIENTE_INVALIDO"


class ClienteNoEncontrado(ClienteException):
    codigo = "CLIENTE_NO_ENCONTRADO"

    def __init__(self, identificador):
        super().__init__(f"Cliente no encontrado: {identificador}")


class DNIYaRegistrado(ClienteException):
    codigo = "DNI_YA_REGISTRADO"

    def __init__(self, dni: str):
        super().__init__(f"El DNI {dni} ya esta registrado")

