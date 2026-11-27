"""Vista de inicio de sesion (usa el caso de uso AutenticarUsuario)."""
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render

from src.modules.identity.application.use_cases.autenticar_usuario import AutenticarUsuario
from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioException
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.identity.presentation.forms.login_form import LoginForm
from src.modules.identity.presentation.views.session_login import destino_seguro, establecer_sesion


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
                    from src.modules.identity.domain.exceptions.usuario_exceptions import (
                        CredencialesInvalidas,
                    )
                    from src.modules.identity.infrastructure.persistence.django_models.usuario_model import (
                        UsuarioModel,
                    )
                    coincidencias = list(UsuarioModel.objects.filter(email__iexact=identificador)[:2])
                    if len(coincidencias) != 1:
                        raise CredencialesInvalidas()
                    identificador = coincidencias[0].username
                usuario = caso.ejecutar(identificador, form.cleaned_data["password"])
            except UsuarioException as exc:
                messages.error(request, str(exc))
            else:
                try:
                    establecer_sesion(request, usuario)
                except UsuarioException as exc:
                    messages.error(request, str(exc))
                    return render_login(request, form)
                messages.success(request, f"Bienvenido {usuario.nombre_completo}")
                return redirect(destino_seguro(request, request.GET.get("next", "")))
    else:
        form = LoginForm()

    return render_login(request, form)


def render_login(request, form):
    respuesta = render(request, "identity/login.html", contexto_login(form))
    if settings.FIREBASE_GOOGLE_ENABLED:
        # Solo esta página necesita comunicación con la ventana OAuth de Google.
        respuesta["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    respuesta["Cache-Control"] = "no-store"
    return respuesta


def contexto_login(form):
    return {"form": form, "firebase_enabled": settings.FIREBASE_GOOGLE_ENABLED,
            "firebase_config": settings.FIREBASE_WEB_CONFIG}

