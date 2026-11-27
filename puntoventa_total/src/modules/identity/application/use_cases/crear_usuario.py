"""Caso de uso: alta de usuario con validacion de duplicados."""
from __future__ import annotations

from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.application.ports.password_hasher_port import PasswordHasherPort
from src.modules.identity.domain.entities.usuario import Usuario
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.identity.domain.exceptions.usuario_exceptions import UsernameDuplicado
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository


class CrearUsuario:
    def __init__(self, repo: UsuarioRepository, hasher: PasswordHasherPort):
        self._repo = repo
        self._hasher = hasher

    def ejecutar(self, datos: UsuarioInputDTO) -> UsuarioOutputDTO:
        if self._repo.buscar_por_username(datos.username.strip().lower()):
            raise UsernameDuplicado(datos.username)

        usuario = Usuario(
            username=datos.username.strip().lower(),
            password_hash=self._hasher.hash(datos.password),
            nombre_completo=datos.nombre_completo.strip(),
            email=datos.email.strip(),
            rol=RolUsuario(datos.rol),
        )
        self._repo.guardar(usuario)
        return UsuarioOutputDTO.desde_entidad(usuario)

