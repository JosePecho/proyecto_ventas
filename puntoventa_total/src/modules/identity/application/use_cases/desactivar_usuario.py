"""Caso de uso: baja logica sin perder auditoria."""
from __future__ import annotations

from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioNoEncontrado
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository


class DesactivarUsuario:
    def __init__(self, repo: UsuarioRepository):
        self._repo = repo

    def ejecutar(self, usuario_id: str, motivo: str = "") -> UsuarioOutputDTO:
        usuario = self._repo.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoEncontrado(usuario_id)
        if usuario.es_administrador():
            from src.shared.domain.exceptions.validation_exception import ValidationException

            ultimos = [u for u in self._repo.listar() if u.es_administrador() and u.activo]
            if len(ultimos) <= 1:
                raise ValidationException("No se puede desactivar al ultimo administrador")

        usuario.desactivar(motivo)
        self._repo.guardar(usuario)
        return UsuarioOutputDTO.desde_entidad(usuario)

