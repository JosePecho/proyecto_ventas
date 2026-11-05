"""Establecimiento compartido de la sesión local."""
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def establecer_sesion(request, usuario, *, google=False):
    user, _ = User.objects.get_or_create(
        username=usuario.username,
        defaults={"is_staff": not google and usuario.rol == "ADMINISTRADOR"},
    )
    if not user.is_active:
        from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioInactivo

        raise UsuarioInactivo()
    user.first_name = usuario.nombre_completo
    user.save()
    login(request, user)
    request.session["rol"] = usuario.rol
    request.session["identity_role"] = usuario.rol
    request.session["usuario_id"] = usuario.id
    request.session.pop("cliente_id", None)
    if usuario.rol == "CLIENTE":
        from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel

        cliente_id = ClienteModel.objects.filter(usuario_id=usuario.id, activo=True).values_list("id", flat=True).first()
        if cliente_id:
            request.session["cliente_id"] = str(cliente_id)


def destino_seguro(request, destino):
    if not url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return reverse("catalog:catalogo")
    return destino
