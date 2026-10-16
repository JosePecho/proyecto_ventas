"""Violacion de invariantes de valor/entidad."""
from .domain_exception import DomainException


class ValidationException(DomainException):
    codigo = "VALIDACION_FALLIDA"

