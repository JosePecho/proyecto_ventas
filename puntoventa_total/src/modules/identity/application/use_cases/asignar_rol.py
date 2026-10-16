"""Caso de uso: cambio de rol con control de privilegio maximo."""
from __future__ import annotations

from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioNoEncontrado
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository


class AsignarRol:
    def __init__(self, repo: UsuarioRepository):
        self._repo = repo

    def ejecutar(self, usuario_id: str, nuevo_rol: str, operador_es_admin: bool) -> UsuarioOutputDTO:
        from src.shared.domain.exceptions.validation_exception import ValidationException

        if RolUsuario(nuevo_rol) == RolUsuario.ADMINISTRADOR and not operador_es_admin:
            raise ValidationException("Solo un administrador puede asignar el rol Administrador")

        usuario = self._repo.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoEncontrado(usuario_id)

        usuario.cambiar_rol(RolUsuario(nuevo_rol))
        self._repo.guardar(usuario)
        return UsuarioOutputDTO.desde_entidad(usuario)

