"""Autentica únicamente vinculaciones Google previamente autorizadas."""
from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.application.ports.google_identity_port import GoogleIdentityPort
from src.modules.identity.application.ports.google_vinculo_port import GoogleVinculoPort
from src.modules.identity.domain.exceptions.usuario_exceptions import CredencialesInvalidas, UsuarioInactivo
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository


class AutenticarGoogle:
    def __init__(self, repo: UsuarioRepository, verificador: GoogleIdentityPort, vinculos: GoogleVinculoPort):
        self._repo = repo
        self._verificador = verificador
        self._vinculos = vinculos

    def ejecutar(self, token: str) -> UsuarioOutputDTO:
        identidad = self._verificador.verificar(token)
        return self.por_identidad(identidad)

    def por_identidad(self, identidad) -> UsuarioOutputDTO:
        usuario = self._vinculos.buscar_usuario(identidad)
        if usuario is None:
            raise CredencialesInvalidas()
        if not usuario.puede_autenticarse():
            raise UsuarioInactivo()
        usuario.registrar_acceso_exitoso()
        self._repo.guardar(usuario)
        return UsuarioOutputDTO.desde_entidad(usuario)
