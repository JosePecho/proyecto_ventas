"""Verificación criptográfica mediante Firebase Admin; nunca registra tokens."""
import os
from threading import Lock

import firebase_admin
from django.conf import settings
from firebase_admin import auth, credentials

from src.modules.identity.application.dto.google_identity import GoogleIdentity
from src.modules.identity.application.ports.google_identity_port import (
    GoogleIdentityPort,
    GoogleNoDisponible,
    GoogleTokenInvalido,
)

_lock = Lock()


def obtener_firebase_app():
    if os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"):
        raise GoogleNoDisponible()
    with _lock:
        try:
            return firebase_admin.get_app("puntoventa-google")
        except ValueError:
            try:
                credencial = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
                if credencial.project_id != settings.FIREBASE_PROJECT_ID:
                    raise GoogleNoDisponible()
                return firebase_admin.initialize_app(
                    credencial, {"projectId": settings.FIREBASE_PROJECT_ID, "httpTimeout": 10},
                    name="puntoventa-google",
                )
            except (OSError, ValueError):
                raise GoogleNoDisponible() from None


class FirebaseGoogleAdapter(GoogleIdentityPort):
    def verificar(self, token: str) -> GoogleIdentity:
        try:
            claims = auth.verify_id_token(token, app=obtener_firebase_app(), check_revoked=True)
        except (auth.InvalidIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError, ValueError):
            raise GoogleTokenInvalido() from None
        except GoogleNoDisponible:
            raise
        except Exception:
            raise GoogleNoDisponible() from None
        email = claims.get("email", "")
        if (claims.get("firebase", {}).get("sign_in_provider") != "google.com"
                or claims.get("email_verified") is not True or not isinstance(email, str)
                or not email.lower().endswith("@gmail.com")):
            # Firebase no garantiza incluir el claim hd de Google Workspace.
            # Sin vinculación previa, solo Gmail permite asociación segura por correo.
            raise GoogleTokenInvalido()
        uid = claims.get("uid")
        if not isinstance(uid, str) or not uid or len(uid) > 128:
            raise GoogleTokenInvalido()
        nombre = claims.get("name", "")
        if not isinstance(nombre, str):
            nombre = ""
        return GoogleIdentity(uid=uid, email=email.strip().lower(), nombre=nombre[:120],
                              proyecto=settings.FIREBASE_PROJECT_ID, auth_time=claims.get("auth_time", 0))

    def revalidar(self, identidad: GoogleIdentity):
        """Revisa baja, revocación y cambios de correo al completar una operación pendiente."""
        try:
            usuario = auth.get_user(identidad.uid, app=obtener_firebase_app())
        except auth.UserNotFoundError:
            raise GoogleTokenInvalido() from None
        except Exception:
            raise GoogleNoDisponible() from None
        correos_google = [p.email.lower() for p in usuario.provider_data if p.provider_id == "google.com" and p.email]
        if (usuario.disabled or not usuario.email_verified or not usuario.email
                or usuario.email.lower() != identidad.email or identidad.email not in correos_google
                or usuario.tokens_valid_after_timestamp > identidad.auth_time * 1000):
            raise GoogleTokenInvalido()
