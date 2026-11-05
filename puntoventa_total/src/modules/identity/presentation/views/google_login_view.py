"""Acceso, alta y vinculación con Google sin almacenar ID tokens."""
import json
import time
from dataclasses import asdict

from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods, require_POST

from src.modules.identity.application.dto.google_identity import GoogleIdentity
from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.application.ports.google_identity_port import (
    GoogleNoDisponible,
    GoogleTokenInvalido,
)
from src.modules.identity.application.use_cases.autenticar_google import AutenticarGoogle
from src.modules.identity.infrastructure.factories import construir_repositorio
from src.modules.identity.infrastructure.google_registration_service import (
    autenticar_para_vincular,
    completar_google,
    necesita_perfil,
    perfil_cliente,
    resolver_google,
    vincular_google,
)
from src.modules.identity.infrastructure.persistence.repositories.google_vinculo_repository import (
    GoogleVinculoRepository,
)
from src.modules.identity.infrastructure.security.firebase_google_adapter import FirebaseGoogleAdapter
from src.modules.identity.presentation.forms.google_forms import CompletarGoogleForm, VincularGoogleForm
from src.modules.identity.presentation.views.session_login import establecer_sesion
from src.shared.domain.exceptions.domain_exception import DomainException

PENDIENTE = "google_registro_pendiente"
CADUCIDAD = 600
ERROR_CUENTA = "No se pudo autorizar esta cuenta. Usa tu acceso tradicional o contacta al administrador."


def guardar_pendiente(request, identidad, paso):
    request.session.cycle_key()
    request.session[PENDIENTE] = {"identidad": asdict(identidad), "paso": paso, "vence": time.time() + CADUCIDAD}


def leer_pendiente(request, paso):
    datos = request.session.get(PENDIENTE)
    if (not settings.FIREBASE_GOOGLE_ENABLED or not isinstance(datos, dict)
            or datos.get("vence", 0) < time.time() or datos.get("paso") != paso
            or request.user.is_authenticated):
        raise GoogleTokenInvalido()
    identidad = GoogleIdentity(**datos["identidad"])
    if identidad.proyecto != settings.FIREBASE_PROJECT_ID:
        raise GoogleTokenInvalido()
    return identidad


def pendiente_invalido(request):
    request.session.pop(PENDIENTE, None)
    messages.error(request, "La solicitud de Google caducó o ya no es válida. Inicia el proceso otra vez.")
    return redirect("identity:login")


def render_datos(request, form, *, vincular=False):
    return render(request, "identity/google_datos.html", {
        "form": form,
        "titulo": "Vincula tu cuenta" if vincular else "Completa tus datos",
        "explicacion": ("Ya existe una cuenta con este correo. Confirma tu usuario y contraseña para vincular Google."
                        if vincular else "Solo falta completar tus datos para continuar al catálogo."),
        "boton": "Vincular y continuar" if vincular else "Guardar y continuar",
    })


@never_cache
@require_POST
@sensitive_post_parameters()
@sensitive_variables("token", "datos")
def google_login_view(request):
    if not settings.FIREBASE_GOOGLE_ENABLED:
        return JsonResponse({"error": "El acceso con Google no está disponible."}, status=503)
    if request.user.is_authenticated:
        return JsonResponse({"error": "Cierra tu sesión antes de cambiar de cuenta."}, status=409)
    if request.content_type != "application/json" or len(request.body) > 16384:
        return JsonResponse({"error": "Solicitud inválida."}, status=400)
    try:
        datos = json.loads(request.body)
        token = datos.get("id_token") if isinstance(datos, dict) else None
        if not isinstance(token, str) or not token or len(token) > 12000:
            raise ValueError()
        if not isinstance(datos.get("next", ""), str):
            raise ValueError()
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Solicitud inválida."}, status=400)
    try:
        identidad = FirebaseGoogleAdapter().verificar(token)
        paso, _usuario = resolver_google(identidad)
        if paso == "entrar":
            usuario = AutenticarGoogle(construir_repositorio(), FirebaseGoogleAdapter(),
                                      GoogleVinculoRepository()).por_identidad(identidad)
            establecer_sesion(request, usuario, google=True)
            return JsonResponse({"redirect": reverse("catalog:catalogo")})
        guardar_pendiente(request, identidad, paso)
        return JsonResponse({"redirect": reverse("identity:google_" + paso)})
    except (GoogleTokenInvalido, DomainException, IntegrityError):
        return JsonResponse({"error": ERROR_CUENTA}, status=403)
    except GoogleNoDisponible:
        return JsonResponse({"error": "Google no está disponible temporalmente. Usa tu acceso tradicional."}, status=503)


@never_cache
@require_http_methods(["GET", "POST"])
@sensitive_post_parameters("password")
def google_vincular_view(request):
    try:
        identidad = leer_pendiente(request, "vincular")
    except (GoogleTokenInvalido, TypeError, KeyError):
        return pendiente_invalido(request)
    form = VincularGoogleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            FirebaseGoogleAdapter().revalidar(identidad)
            dto = autenticar_para_vincular(identidad, form.cleaned_data["username"], form.cleaned_data["password"])
            with transaction.atomic():
                usuario = vincular_google(identidad, dto.id)
                if necesita_perfil(usuario):
                    guardar_pendiente(request, identidad, "completar")
                    return redirect("identity:google_completar")
                establecer_sesion(request, UsuarioOutputDTO.desde_entidad(usuario), google=True)
            return redirect("catalog:catalogo")
        except GoogleNoDisponible:
            form.add_error(None, "No se pudo consultar Google. Inténtalo de nuevo sin cambiar de cuenta.")
        except (GoogleTokenInvalido, DomainException, IntegrityError):
            form.add_error(None, "No se pudo vincular. Revisa tus credenciales o contacta al administrador.")
    return render_datos(request, form, vincular=True)


@never_cache
@require_http_methods(["GET", "POST"])
@sensitive_post_parameters()
def google_completar_view(request):
    try:
        identidad = leer_pendiente(request, "completar")
        paso, usuario = resolver_google(identidad)
        if paso == "vincular":
            guardar_pendiente(request, identidad, "vincular")
            return redirect("identity:google_vincular")
        perfil = perfil_cliente(usuario) if usuario else None
    except (GoogleTokenInvalido, DomainException, TypeError, KeyError):
        return pendiente_invalido(request)
    initial = {"nombre": identidad.nombre, "email": identidad.email}
    if perfil:
        initial.update({campo: getattr(perfil, campo) for campo in ("nombre", "dni", "telefono", "direccion")})
    form = CompletarGoogleForm(request.POST or None, email=identidad.email,
                              cliente_id=perfil.id if perfil else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            FirebaseGoogleAdapter().revalidar(identidad)
            with transaction.atomic():
                dto = completar_google(identidad, form.cleaned_data)
                establecer_sesion(request, dto, google=True)
            return redirect("catalog:catalogo")
        except GoogleNoDisponible:
            form.add_error(None, "No se pudo consultar Google. Inténtalo de nuevo.")
        except (GoogleTokenInvalido, DomainException, IntegrityError):
            form.add_error(None, "No se pudo completar el registro. Revisa tus datos o contacta al administrador.")
    return render_datos(request, form)


@never_cache
@require_POST
def google_cancelar_view(request):
    request.session.pop(PENDIENTE, None)
    return redirect("identity:login")
