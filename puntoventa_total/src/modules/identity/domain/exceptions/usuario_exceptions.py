"""Reglas de negocio especificas de usuarios."""
from src.shared.domain.exceptions.domain_exception import DomainException


class UsuarioException(DomainException):
    codigo = "USUARIO_INVALIDO"


class UsuarioNoEncontrado(UsuarioException):
    codigo = "USUARIO_NO_ENCONTRADO"

    def __init__(self, identificador):
        super().__init__(f"Usuario no encontrado: {identificador}")


class CredencialesInvalidas(UsuarioException):
    codigo = "CREDENCIALES_INVALIDAS"

    def __init__(self):
        super().__init__("Usuario o contrasena incorrectos")


class UsuarioInactivo(UsuarioException):
    codigo = "USUARIO_INACTIVO"

    def __init__(self):
        super().__init__("El usuario se encuentra desactivado")


class UsernameDuplicado(UsuarioException):
    codigo = "USERNAME_DUPLICADO"

    def __init__(self, username: str):
        super().__init__(f"Ya existe un usuario con el nombre '{username}'")

