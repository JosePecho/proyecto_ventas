from src.modules.identity.application.ports.google_vinculo_port import GoogleVinculoPort
from src.modules.identity.infrastructure.persistence.django_models.google_vinculo_model import (
    GoogleVinculoModel,
    clave_google,
)
from src.modules.identity.infrastructure.persistence.mappers.usuario_mapper import UsuarioMapper


class GoogleVinculoRepository(GoogleVinculoPort):
    def buscar_usuario(self, identidad):
        vinculo = GoogleVinculoModel.objects.select_related("usuario").filter(
            clave=clave_google(identidad.proyecto, identidad.uid)).first()
        if vinculo is None:
            return None
        return UsuarioMapper().a_dominio(vinculo.usuario)
