"""Regresiones de sesión y autorización; Firebase remoto se sustituye en la frontera."""
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import Client

from src.modules.identity.application.ports.google_identity_port import (
    GoogleNoDisponible,
    GoogleTokenInvalido,
)
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
VERIFICAR = "src.modules.identity.infrastructure.security.firebase_google_adapter.FirebaseGoogleAdapter.verificar"
PASSWORD = "Segura!Prueba#725"


@pytest.fixture(autouse=True)
def habilitar(settings):
    settings.FIREBASE_GOOGLE_ENABLED = True


@pytest.fixture
def usuario():
    return UsuarioModel.objects.create(id=uuid4(), username="ana.google", email="ana@gmail.com",
        nombre_completo="Ana Prueba", password_hash=make_password(PASSWORD), rol="CAJERO", estado="ACTIVO")


def google(client, **datos):
    return client.post("/login/google/", {"id_token": "token-de-prueba", **datos}, content_type="application/json")


@pytest.mark.parametrize("rol", ["CAJERO", "GERENTE", "ALMACENERO", "CLIENTE", "ADMINISTRADOR"])
def test_google_conserva_roles_sin_conceder_staff(client, usuario, rol):
    hash_original = usuario.password_hash
    usuario.rol = rol
    usuario.save()
    with patch(VERIFICAR, return_value="ANA@gmail.com"):
        respuesta = google(client)
    assert respuesta.status_code == 200
    assert client.session["rol"] == client.session["identity_role"] == rol
    assert client.session["usuario_id"] == str(usuario.id)
    assert not User.objects.get(username=usuario.username).is_staff
    usuario.refresh_from_db()
    assert usuario.ultimo_acceso is not None
    assert usuario.password_hash == hash_original


@pytest.mark.parametrize("estado,activo", [("BLOQUEADO", True), ("INACTIVO", False), ("ACTIVO", False)])
def test_google_rechaza_cuenta_no_autorizada(client, usuario, estado, activo):
    usuario.estado, usuario.activo = estado, activo
    usuario.save()
    with patch(VERIFICAR, return_value=usuario.email):
        assert google(client).status_code == 403
    assert "_auth_user_id" not in client.session
    assert not User.objects.exists()


def test_desconocido_no_crea_usuarios(client):
    with patch(VERIFICAR, return_value="desconocido@gmail.com"):
        assert google(client).status_code == 403
    assert not UsuarioModel.objects.exists()
    assert not User.objects.exists()


def test_correo_duplicado_rechazado(client, usuario):
    UsuarioModel.objects.create(id=uuid4(), username="duplicado", email="ANA@GMAIL.COM",
        nombre_completo="Otro usuario", password_hash="x", rol="ADMINISTRADOR", estado="ACTIVO")
    with patch(VERIFICAR, return_value=usuario.email):
        assert google(client).status_code == 403
    assert "_auth_user_id" not in client.session


@pytest.mark.parametrize("error,status", [(GoogleTokenInvalido(), 403), (GoogleNoDisponible(), 503)])
def test_error_verificador_no_inicia_sesion(client, usuario, error, status):
    with patch(VERIFICAR, side_effect=error):
        assert google(client).status_code == status
    assert "_auth_user_id" not in client.session


def test_csrf_y_metodo():
    client = Client(enforce_csrf_checks=True)
    assert client.get("/login/google/").status_code == 405
    assert google(client).status_code == 403


def test_google_csrf_valido_y_destino_seguro(usuario):
    client = Client(enforce_csrf_checks=True)
    client.get("/login/")
    with patch(VERIFICAR, return_value=usuario.email):
        respuesta = client.post("/login/google/", {"id_token": "token", "next": "https://malicioso.test"},
            content_type="application/json", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
    assert respuesta.status_code == 200
    assert respuesta.json()["redirect"] == "/catalogo/"
    assert client.post("/logout/", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code == 302
    assert "_auth_user_id" not in client.session


@pytest.mark.parametrize("identificador", ["ana.google", "ANA@GMAIL.COM"])
def test_login_tradicional_sigue_funcionando(client, usuario, identificador):
    respuesta = client.post("/login/", {"username": identificador, "password": PASSWORD})
    assert respuesta.status_code == 302
    assert client.session["usuario_id"] == str(usuario.id)
    assert client.session["rol"] == usuario.rol


def test_password_incorrecta_sigue_rechazada(client, usuario):
    assert client.post("/login/", {"username": usuario.username, "password": "incorrecta"}).status_code == 200
    assert "_auth_user_id" not in client.session


def test_pagina_google_preserva_formulario_y_permite_popup(client):
    respuesta = client.get("/login/")
    assert respuesta["Cross-Origin-Opener-Policy"] == "same-origin-allow-popups"
    assert respuesta["Cache-Control"] == "no-store"
    assert b'name="password"' in respuesta.content
    assert b'name="username"' in respuesta.content
    assert b'id="google-login"' in respuesta.content


def test_google_deshabilitado_conserva_login(client, settings, usuario):
    settings.FIREBASE_GOOGLE_ENABLED = False
    assert b'id="google-login"' not in client.get("/login/").content
    assert google(client).status_code == 503
    assert client.post("/login/", {"username": usuario.username, "password": PASSWORD}).status_code == 302


def test_usuario_django_inactivo_no_puede_entrar(client, usuario):
    User.objects.create_user(username=usuario.username, is_active=False)
    with patch(VERIFICAR, return_value=usuario.email):
        assert google(client).status_code == 403
    assert "_auth_user_id" not in client.session


def test_google_conserva_cliente_id(client, usuario):
    from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel

    usuario.rol = "CLIENTE"
    usuario.save()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Ana", email=usuario.email, usuario_id=usuario.id)
    with patch(VERIFICAR, return_value=usuario.email):
        assert google(client).status_code == 200
    assert client.session["cliente_id"] == str(cliente.id)


@pytest.mark.parametrize("datos", [{}, {"id_token": 1}, {"id_token": "x", "next": []}, []])
def test_solicitud_invalida(client, datos):
    assert client.post("/login/google/", datos, content_type="application/json").status_code == 400


def test_desactivacion_local_invalida_sesion_google(client, usuario):
    with patch(VERIFICAR, return_value=usuario.email):
        assert google(client).status_code == 200
    usuario.activo = False
    usuario.save()
    assert client.get("/catalogo/").status_code == 302
    assert "_auth_user_id" not in client.session
