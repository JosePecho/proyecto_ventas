"""Errores de orquestacion (casos de uso) y de infraestructura."""
from src.shared.domain.exceptions.domain_exception import DomainException


class ApplicationException(DomainException):
    codigo = "APLICACION_FALLIDA"


class ConflictException(ApplicationException):
    codigo = "CONFLICTO"


class NotFoundException(ApplicationException):
    codigo = "NO_ENCONTRADO"


class BusinessException(ApplicationException):
    codigo = "REGLA_NEGOCIO"

