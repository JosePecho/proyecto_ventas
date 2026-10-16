"""Caso de uso: consulta de permisos efectivos de un usuario."""
from __future__ import annotations

from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioNoEncontrado
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository
from src.modules.identity.domain.services.politica_permisos import PoliticaPermisos


class VerificarPermisos:
    def __init__(self, repo: UsuarioRepository):
        self._repo = repo

    def ejecutar(self, usuario_id: str) -> list[str]:
        usuario = self._repo.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoEncontrado(usuario_id)
        return sorted(PoliticaPermisos.permisos_de(usuario.rol))

    def puede(self, usuario_id: str, permiso: str) -> bool:
        usuario = self._repo.buscar_por_id(usuario_id)
        return bool(usuario and PoliticaPermisos.puede(usuario.rol, permiso))

