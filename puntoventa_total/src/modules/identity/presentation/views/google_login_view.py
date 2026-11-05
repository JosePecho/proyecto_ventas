"""POST JSON con ID token y CSRF; la sesión sigue perteneciendo a Django."""
import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_POST

from src.modules.identity.application.ports.google_identity_port import (
    GoogleNoDisponible,
    GoogleTokenInvalido,
)
from src.modules.identity.application.use_cases.autenticar_google import AutenticarGoogle
from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioException
from src.modules.identity.infrastructure.factories import construir_repositorio
from src.modules.identity.infrastructure.security.firebase_google_adapter import FirebaseGoogleAdapter
from src.modules.identity.presentation.views.session_login import destino_seguro, establecer_sesion


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
        destino = datos.get("next", "")
        if not isinstance(destino, str):
            raise ValueError()
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Solicitud inválida."}, status=400)
    try:
        usuario = AutenticarGoogle(construir_repositorio(), FirebaseGoogleAdapter()).ejecutar(token)
        establecer_sesion(request, usuario, google=True)
    except (GoogleTokenInvalido, UsuarioException):
        return JsonResponse({"error": "No se pudo autorizar esta cuenta. Usa tu acceso tradicional o contacta al administrador."}, status=403)
    except GoogleNoDisponible:
        return JsonResponse({"error": "Google no está disponible temporalmente. Usa tu acceso tradicional."}, status=503)
    return JsonResponse({"redirect": destino_seguro(request, destino)})
