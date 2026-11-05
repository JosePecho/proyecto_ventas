"""Autoriza únicamente identidades ya registradas en el sistema."""
from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.application.ports.google_identity_port import GoogleIdentityPort
from src.modules.identity.domain.exceptions.usuario_exceptions import CredencialesInvalidas, UsuarioInactivo
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository


class AutenticarGoogle:
    def __init__(self, repo: UsuarioRepository, verificador: GoogleIdentityPort):
        self._repo = repo
        self._verificador = verificador

    def ejecutar(self, token: str) -> UsuarioOutputDTO:
        email = self._verificador.verificar(token)
        usuario = self._repo.buscar_por_email_unico(email)
        if usuario is None:
            raise CredencialesInvalidas()
        if not usuario.puede_autenticarse():
            raise UsuarioInactivo()
        usuario.registrar_acceso_exitoso()
        self._repo.guardar(usuario)
        return UsuarioOutputDTO.desde_entidad(usuario)
