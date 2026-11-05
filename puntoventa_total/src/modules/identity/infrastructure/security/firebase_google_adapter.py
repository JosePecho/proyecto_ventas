"""Verificación criptográfica mediante Firebase Admin; nunca registra tokens."""
import os
from threading import Lock

import firebase_admin
from django.conf import settings
from firebase_admin import auth, credentials

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
    def verificar(self, token: str) -> str:
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
        return email.strip().lower()
