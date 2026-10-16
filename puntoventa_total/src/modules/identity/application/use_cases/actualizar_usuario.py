"""Caso de uso: actualizar datos y/o password de un usuario."""
from __future__ import annotations

from src.modules.identity.application.dto.usuario_input import ActualizarUsuarioDTO
from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.application.ports.password_hasher_port import PasswordHasherPort
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioNoEncontrado
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository


class ActualizarUsuario:
    def __init__(self, repo: UsuarioRepository, hasher: PasswordHasherPort):
        self._repo = repo
        self._hasher = hasher

    def ejecutar(self, datos: ActualizarUsuarioDTO) -> UsuarioOutputDTO:
        usuario = self._repo.buscar_por_id(datos.usuario_id)
        if usuario is None:
            raise UsuarioNoEncontrado(datos.usuario_id)

        if datos.nombre_completo:
            usuario.nombre_completo = datos.nombre_completo.strip()
        if datos.email:
            usuario.email = datos.email.strip()
        if datos.rol:
            usuario.cambiar_rol(RolUsuario(datos.rol))
        if datos.password_nueva:
            usuario.cambiar_password(self._hasher.hash(datos.password_nueva))

        usuario.marcar_actualizado()
        self._repo.guardar(usuario)
        return UsuarioOutputDTO.desde_entidad(usuario)

