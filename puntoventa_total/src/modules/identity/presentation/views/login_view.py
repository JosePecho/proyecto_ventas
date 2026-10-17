"""Vista de inicio de sesion (usa el caso de uso AutenticarUsuario)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from src.modules.identity.application.use_cases.autenticar_usuario import AutenticarUsuario
from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioException
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.identity.presentation.forms.login_form import LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("catalog:catalogo")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            caso = AutenticarUsuario(construir_repositorio(), construir_hasher())
            try:
                identificador = form.cleaned_data["username"].strip()
                if "@" in identificador:
                    from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
                    from src.modules.identity.domain.exceptions.usuario_exceptions import CredencialesInvalidas
                    coincidencias = list(UsuarioModel.objects.filter(email__iexact=identificador)[:2])
                    if len(coincidencias) != 1:
                        raise CredencialesInvalidas()
                    identificador = coincidencias[0].username
                usuario = caso.ejecutar(identificador, form.cleaned_data["password"])
            except UsuarioException as exc:
                messages.error(request, str(exc))
            else:
                from django.contrib.auth.models import User

                user, _ = User.objects.get_or_create(
                    username=usuario.username,
                    defaults={"is_staff": usuario.rol == "ADMINISTRADOR"},
                )
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
                messages.success(request, f"Bienvenido {usuario.nombre_completo}")
                destino = request.GET.get("next", "")
                if not url_has_allowed_host_and_scheme(
                    destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
                ):
                    destino = "catalog:catalogo"
                return redirect(destino)
    else:
        form = LoginForm()

    return render(request, "identity/login.html", {"form": form})

