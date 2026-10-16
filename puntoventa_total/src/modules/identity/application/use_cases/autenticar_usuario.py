"""Caso de uso: autenticar credenciales y registrar intentos."""
from __future__ import annotations

from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.application.ports.password_hasher_port import PasswordHasherPort
from src.modules.identity.domain.entities.usuario import Usuario
from src.modules.identity.domain.exceptions.usuario_exceptions import (
    CredencialesInvalidas,
    UsuarioInactivo,
)
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository


class AutenticarUsuario:
    def __init__(self, repo: UsuarioRepository, hasher: PasswordHasherPort):
        self._repo = repo
        self._hasher = hasher

    def ejecutar(self, username: str, password: str) -> UsuarioOutputDTO:
        usuario = self._repo.buscar_por_username(username.strip())
        if usuario is None:
            raise CredencialesInvalidas()

        if not usuario.puede_autenticarse():
            raise UsuarioInactivo()

        if not self._hasher.verificar(password, usuario.password_hash):
            usuario.registrar_intentofallido()
            self._repo.guardar(usuario)
            raise CredencialesInvalidas()

        usuario.registrar_acceso_exitoso()
        self._repo.guardar(usuario)
        return UsuarioOutputDTO.desde_entidad(usuario)

