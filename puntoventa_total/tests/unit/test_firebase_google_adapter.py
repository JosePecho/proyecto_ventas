from types import SimpleNamespace
from unittest.mock import patch

import pytest
from firebase_admin import auth

from src.modules.identity.application.dto.google_identity import GoogleIdentity
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
    claims = {"uid": "uid-ana", "auth_time": 123, "email": "ANA@gmail.com", "email_verified": True,
              "firebase": {"sign_in_provider": "google.com"}}
    with patch(f"{MODULO}.obtener_firebase_app", return_value="app"), \
            patch(f"{MODULO}.auth.verify_id_token", return_value=claims) as verificar:
        identidad = FirebaseGoogleAdapter().verificar("token")
        assert identidad.email == "ana@gmail.com" and identidad.uid == "uid-ana"
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


@pytest.mark.parametrize("cambio", [
    {"disabled": True}, {"email_verified": False}, {"email": "otro@gmail.com"},
    {"tokens_valid_after_timestamp": 124000}, {"provider_data": []},
])
def test_revalidacion_no_permite_cambios_de_identidad(cambio):
    identidad = GoogleIdentity(uid="ana", email="ana@gmail.com", nombre="Ana", proyecto="puntoventa-a7f93", auth_time=123)
    registro = SimpleNamespace(**{"disabled": False, "email_verified": True, "email": "ana@gmail.com",
        "tokens_valid_after_timestamp": 123000,
        "provider_data": [SimpleNamespace(provider_id="google.com", email="ana@gmail.com")], **cambio})
    with patch(f"{MODULO}.obtener_firebase_app"), patch(f"{MODULO}.auth.get_user", return_value=registro):
        with pytest.raises(GoogleTokenInvalido):
            FirebaseGoogleAdapter().revalidar(identidad)


def test_revalidacion_identidad_vigente():
    identidad = GoogleIdentity(uid="ana", email="ana@gmail.com", nombre="Ana", proyecto="puntoventa-a7f93", auth_time=123)
    registro = SimpleNamespace(disabled=False, email_verified=True, email="ana@gmail.com",
        tokens_valid_after_timestamp=123000,
        provider_data=[SimpleNamespace(provider_id="google.com", email="ana@gmail.com")])
    with patch(f"{MODULO}.obtener_firebase_app", return_value="app"), \
            patch(f"{MODULO}.auth.get_user", return_value=registro) as get_user:
        FirebaseGoogleAdapter().revalidar(identidad)
        get_user.assert_called_once_with("ana", app="app")
