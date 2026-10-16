"""Fabrica de dependencias del modulo identidad (composition root local)."""
from src.modules.identity.application.ports.password_hasher_port import PasswordHasherPort
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository
from src.modules.identity.infrastructure.persistence.repositories.django_usuario_repository import (
    DjangoUsuarioRepository,
)
from src.modules.identity.infrastructure.security.django_auth_adapter import DjangoAuthAdapter


def construir_repositorio() -> UsuarioRepository:
    return DjangoUsuarioRepository()


def construir_hasher() -> PasswordHasherPort:
    return DjangoAuthAdapter()

