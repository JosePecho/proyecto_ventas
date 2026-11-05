from unittest.mock import patch

import pytest
from firebase_admin import auth

from src.modules.identity.application.ports.google_identity_port import (
    GoogleNoDisponible,
    GoogleTokenInvalido,
)
from src.modules.identity.infrastructure.security.firebase_google_adapter import FirebaseGoogleAdapter

pytestmark = pytest.mark.unit
MODULO = "src.modules.identity.infrastructure.security.firebase_google_adapter"


@pytest.mark.parametrize("cambio", [
    {"email_verified": False}, {"email": "ana@example.com"}, {"email": None},
    {"firebase": {"sign_in_provider": "password"}}, {"email": ""},
])
def test_rechaza_identidad_no_garantizada(cambio):
    claims = {"email": "ana@gmail.com", "email_verified": True,
              "firebase": {"sign_in_provider": "google.com"}, **cambio}
    with patch(f"{MODULO}.obtener_firebase_app"), patch(f"{MODULO}.auth.verify_id_token", return_value=claims):
        with pytest.raises(GoogleTokenInvalido):
            FirebaseGoogleAdapter().verificar("token")


def test_solicita_verificacion_y_revocacion():
    claims = {"email": "ANA@gmail.com", "email_verified": True, "firebase": {"sign_in_provider": "google.com"}}
    with patch(f"{MODULO}.obtener_firebase_app", return_value="app"), \
            patch(f"{MODULO}.auth.verify_id_token", return_value=claims) as verificar:
        assert FirebaseGoogleAdapter().verificar("token") == "ana@gmail.com"
        verificar.assert_called_once_with("token", app="app", check_revoked=True)


@pytest.mark.parametrize("error", [auth.InvalidIdTokenError("invalid"), auth.RevokedIdTokenError("revoked"),
                                  auth.UserDisabledError("disabled")])
def test_tokens_invalidos_rechazados(error):
    with patch(f"{MODULO}.obtener_firebase_app"), patch(f"{MODULO}.auth.verify_id_token", side_effect=error):
        with pytest.raises(GoogleTokenInvalido):
            FirebaseGoogleAdapter().verificar("token")


def test_no_permite_emulador(monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
    with pytest.raises(GoogleNoDisponible):
        FirebaseGoogleAdapter().verificar("token")
