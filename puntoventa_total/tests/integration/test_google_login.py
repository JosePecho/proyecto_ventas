"""Registro, vinculación, permisos y rollback con base de datos real de pruebas."""
import time
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth.hashers import is_password_usable, make_password
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import Client

from src.modules.customers.domain.exceptions.cliente_exceptions import DNIYaRegistrado
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.identity.application.dto.google_identity import GoogleIdentity
from src.modules.identity.application.ports.google_identity_port import (
    GoogleNoDisponible,
    GoogleTokenInvalido,
)
from src.modules.identity.infrastructure.persistence.django_models.google_vinculo_model import (
    GoogleVinculoModel,
)
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
VERIFICAR = "src.modules.identity.infrastructure.security.firebase_google_adapter.FirebaseGoogleAdapter.verificar"
REVALIDAR = "src.modules.identity.infrastructure.security.firebase_google_adapter.FirebaseGoogleAdapter.revalidar"
PASSWORD = "Segura!Prueba#725"
PENDIENTE = "google_registro_pendiente"
DATOS = {"nombre": "Ana Cliente", "dni": "12345678", "telefono": "987654321", "direccion": ""}


def identidad(email="ana@gmail.com", uid="uid-google-ana"):
    return GoogleIdentity(uid=uid, email=email, nombre="Ana Cliente", proyecto="puntoventa-a7f93", auth_time=int(time.time()))


@pytest.fixture(autouse=True)
def habilitar(settings):
    settings.FIREBASE_GOOGLE_ENABLED = True


@pytest.fixture
def usuario():
    return UsuarioModel.objects.create(id=uuid4(), username="ana.google", email="ana@gmail.com",
        nombre_completo="Ana Prueba", password_hash=make_password(PASSWORD), rol="CAJERO", estado="ACTIVO")


def vinculo(usuario, quien=None):
    quien = quien or identidad()
    return GoogleVinculoModel.objects.create(usuario=usuario, proyecto=quien.proyecto, uid=quien.uid, email=quien.email)


def google(client, quien=None, **datos):
    with patch(VERIFICAR, return_value=quien or identidad()):
        return client.post("/login/google/", {"id_token": "token-de-prueba", **datos}, content_type="application/json")


def completar(client, datos=None):
    with patch(REVALIDAR):
        return client.post("/login/google/completar/", datos if datos is not None else DATOS)


def vincular(client, datos=None):
    with patch(REVALIDAR):
        return client.post("/login/google/vincular/", datos if datos is not None else {
            "username": "ana.google", "password": PASSWORD, "confirmar": "on"})


@pytest.mark.parametrize("rol", ["CAJERO", "GERENTE", "ALMACENERO", "CLIENTE", "ADMINISTRADOR"])
def test_google_vinculado_conserva_roles_sin_conceder_staff(client, usuario, rol):
    hash_original = usuario.password_hash
    usuario.rol = rol
    usuario.save()
    vinculo(usuario)
    if rol == "CLIENTE":
        ClienteModel.objects.create(id=uuid4(), usuario_id=usuario.id, email=usuario.email, **DATOS)
    respuesta = google(client, next="/reportes/")
    assert respuesta.status_code == 200
    assert respuesta.json()["redirect"] == "/catalogo/"
    assert client.session["rol"] == client.session["identity_role"] == rol
    assert client.session["usuario_id"] == str(usuario.id)
    assert not User.objects.get(username=usuario.username).is_staff
    usuario.refresh_from_db()
    assert usuario.ultimo_acceso is not None
    assert usuario.password_hash == hash_original


@pytest.mark.parametrize("estado,activo", [("BLOQUEADO", True), ("INACTIVO", False), ("ACTIVO", False)])
@pytest.mark.parametrize("vinculado", [True, False])
def test_google_rechaza_cuenta_no_autorizada(client, usuario, estado, activo, vinculado):
    usuario.estado, usuario.activo = estado, activo
    usuario.save()
    if vinculado:
        vinculo(usuario)
    assert google(client).status_code == 403
    assert "_auth_user_id" not in client.session
    assert not User.objects.exists()


def test_nuevo_gmail_pide_datos_sin_crear_cuentas(client):
    respuesta = google(client)
    assert respuesta.json()["redirect"] == "/login/google/completar/"
    assert not UsuarioModel.objects.exists()
    assert not ClienteModel.objects.exists()
    assert not GoogleVinculoModel.objects.exists()
    assert "_auth_user_id" not in client.session
    assert "token-de-prueba" not in str(dict(client.session))
    pagina = client.get(respuesta.json()["redirect"])
    assert pagina.status_code == 200
    assert pagina.context["form"].fields["dni"].required
    assert pagina.context["form"].fields["telefono"].required
    assert pagina.context["form"].fields["email"].disabled


def test_registro_cliente_y_login_posterior_por_uid(client):
    google(client)
    respuesta = completar(client, {**DATOS, "email": "atacante@gmail.com", "rol": "ADMINISTRADOR", "is_staff": "1"})
    assert respuesta.status_code == 302 and respuesta.url == "/catalogo/"
    usuario = UsuarioModel.objects.get()
    assert usuario.rol == "CLIENTE" and usuario.email == "ana@gmail.com"
    assert not is_password_usable(usuario.password_hash)
    cliente = ClienteModel.objects.get()
    assert cliente.usuario_id == usuario.id and cliente.email == usuario.email
    assert client.session["cliente_id"] == str(cliente.id)
    assert PENDIENTE not in client.session
    assert not User.objects.get().is_staff and not User.objects.get().is_superuser
    client.post("/logout/")
    assert google(client).json()["redirect"] == "/catalogo/"
    assert UsuarioModel.objects.count() == ClienteModel.objects.count() == GoogleVinculoModel.objects.count() == 1


@pytest.mark.parametrize("datos", [
    {**DATOS, "dni": ""}, {**DATOS, "dni": "abc"}, {**DATOS, "telefono": ""},
    {**DATOS, "telefono": "123456789"}, {**DATOS, "nombre": ""},
])
def test_registro_exige_politica_actual(client, datos):
    google(client)
    respuesta = completar(client, datos)
    assert respuesta.status_code == 200 and respuesta.context["form"].errors
    assert not UsuarioModel.objects.exists()
    assert not ClienteModel.objects.exists()
    assert "_auth_user_id" not in client.session


def test_dni_existente_no_fusiona_cliente(client):
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente previo", dni=DATOS["dni"])
    google(client)
    assert completar(client).context["form"].errors
    cliente.refresh_from_db()
    assert cliente.usuario_id is None
    assert not UsuarioModel.objects.exists()


@pytest.mark.parametrize("rol", ["CLIENTE", "ADMINISTRADOR", "GERENTE", "CAJERO"])
def test_cuenta_existente_exige_password_y_confirmacion(client, usuario, rol):
    usuario.rol = rol
    usuario.save()
    if rol == "CLIENTE":
        ClienteModel.objects.create(id=uuid4(), usuario_id=usuario.id, email=usuario.email, **DATOS)
    assert google(client).json()["redirect"] == "/login/google/vincular/"
    assert "_auth_user_id" not in client.session
    assert not GoogleVinculoModel.objects.exists()
    assert vincular(client, {"username": usuario.username, "password": PASSWORD}).context["form"].errors
    assert not GoogleVinculoModel.objects.exists()
    respuesta = vincular(client)
    assert respuesta.status_code == 302 and respuesta.url == "/catalogo/"
    assert GoogleVinculoModel.objects.get().usuario_id == usuario.id
    assert client.session["rol"] == rol
    assert UsuarioModel.objects.count() == 1
    assert not User.objects.get().is_staff


def test_password_incorrecto_no_vincula_y_bloquea(client, usuario):
    google(client)
    for _ in range(5):
        assert vincular(client, {"username": usuario.username, "password": "incorrecta", "confirmar": "on"}).status_code == 200
    usuario.refresh_from_db()
    assert usuario.estado == "BLOQUEADO" and usuario.intentos_fallidos == 5
    assert not GoogleVinculoModel.objects.exists()
    assert "_auth_user_id" not in client.session


def test_password_de_otro_usuario_no_vincula(client, usuario):
    UsuarioModel.objects.create(id=uuid4(), username="otro.usuario", email="otro@gmail.com", nombre_completo="Otro",
        password_hash=make_password(PASSWORD), rol="ADMINISTRADOR", estado="ACTIVO")
    google(client)
    assert vincular(client, {"username": "otro.usuario", "password": PASSWORD, "confirmar": "on"}).context["form"].errors
    assert not GoogleVinculoModel.objects.exists()


def test_cliente_previo_sin_perfil_completa_despues_de_vincular(client, usuario):
    usuario.rol = "CLIENTE"
    usuario.save()
    google(client)
    assert vincular(client).url == "/login/google/completar/"
    assert "_auth_user_id" not in client.session
    assert completar(client).url == "/catalogo/"
    assert UsuarioModel.objects.count() == ClienteModel.objects.count() == 1


def test_perfil_incompleto_existente_se_completa_sin_duplicar(client, usuario):
    usuario.rol = "CLIENTE"
    usuario.save()
    vinculo(usuario)
    cliente = ClienteModel.objects.create(id=uuid4(), usuario_id=usuario.id, nombre="Ana", email=usuario.email)
    assert google(client).json()["redirect"] == "/login/google/completar/"
    assert completar(client).url == "/catalogo/"
    cliente.refresh_from_db()
    assert cliente.dni == DATOS["dni"] and cliente.telefono == DATOS["telefono"]
    assert ClienteModel.objects.count() == 1


def test_correo_duplicado_sin_vinculo_rechazado(client, usuario):
    UsuarioModel.objects.create(id=uuid4(), username="duplicado", email="ANA@GMAIL.COM",
        nombre_completo="Otro", password_hash="x", rol="ADMINISTRADOR", estado="ACTIVO")
    assert google(client).status_code == 403
    assert "_auth_user_id" not in client.session


def test_otro_uid_no_hereda_vinculo_por_correo(client, usuario):
    vinculo(usuario)
    assert google(client, identidad(uid="uid-atacante")).status_code == 403
    assert "_auth_user_id" not in client.session


def test_uid_distingue_mayusculas_en_la_base():
    u1 = UsuarioModel.objects.create(id=uuid4(), username="uno.usuario", email="uno@gmail.com", nombre_completo="Uno")
    u2 = UsuarioModel.objects.create(id=uuid4(), username="dos.usuario", email="dos@gmail.com", nombre_completo="Dos")
    vinculo(u1, identidad(email=u1.email, uid="UID-A"))
    vinculo(u2, identidad(email=u2.email, uid="uid-a"))
    assert GoogleVinculoModel.objects.count() == 2


def test_restricciones_evitan_dos_vinculos_por_usuario(usuario):
    vinculo(usuario)
    with pytest.raises(IntegrityError), transaction.atomic():
        vinculo(usuario, identidad(email="otro@gmail.com", uid="otro-uid"))


@pytest.mark.parametrize("error,status", [(GoogleTokenInvalido(), 403), (GoogleNoDisponible(), 503)])
def test_error_verificador_no_inicia_sesion(client, error, status):
    with patch(VERIFICAR, side_effect=error):
        respuesta = client.post("/login/google/", {"id_token": "token"}, content_type="application/json")
    assert respuesta.status_code == status
    assert "_auth_user_id" not in client.session


def test_revocacion_durante_formulario_no_crea_usuario(client):
    google(client)
    with patch(REVALIDAR, side_effect=GoogleTokenInvalido()):
        assert client.post("/login/google/completar/", DATOS).context["form"].errors
    assert not UsuarioModel.objects.exists()


def test_fallo_cliente_revierte_usuario_y_vinculo(client):
    google(client)
    objetivo = "src.modules.identity.infrastructure.google_registration_service.RegistrarCliente.ejecutar"
    with patch(objetivo, side_effect=DNIYaRegistrado(DATOS["dni"])):
        assert completar(client).context["form"].errors
    assert not UsuarioModel.objects.exists()
    assert not GoogleVinculoModel.objects.exists()
    assert not ClienteModel.objects.exists()


def test_aparece_cuenta_mientras_completa_exige_vincular(client):
    google(client)
    UsuarioModel.objects.create(id=uuid4(), username="ana.nueva", email="ana@gmail.com", nombre_completo="Ana",
        password_hash=make_password(PASSWORD), rol="CLIENTE", estado="ACTIVO")
    assert completar(client).url == "/login/google/vincular/"
    assert UsuarioModel.objects.count() == 1
    assert not GoogleVinculoModel.objects.exists()


def test_caducidad_y_cancelacion(client):
    google(client)
    sesion = client.session
    sesion[PENDIENTE] = {**sesion[PENDIENTE], "vence": 0}
    sesion.save()
    assert completar(client).url == "/login/"
    assert PENDIENTE not in client.session
    google(client)
    assert client.post("/login/google/cancelar/").url == "/login/"
    assert PENDIENTE not in client.session
    assert not UsuarioModel.objects.exists()


def test_csrf_y_metodos_todos_los_endpoints():
    client = Client(enforce_csrf_checks=True)
    assert client.get("/login/google/").status_code == 405
    for ruta in ("/login/google/", "/login/google/completar/", "/login/google/vincular/", "/login/google/cancelar/"):
        assert client.post(ruta).status_code == 403


def test_google_csrf_valido_y_destino_catalogo(usuario):
    vinculo(usuario)
    client = Client(enforce_csrf_checks=True)
    client.get("/login/")
    with patch(VERIFICAR, return_value=identidad()):
        respuesta = client.post("/login/google/", {"id_token": "token", "next": "https://malicioso.test"},
            content_type="application/json", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
    assert respuesta.status_code == 200 and respuesta.json()["redirect"] == "/catalogo/"
    assert client.post("/logout/", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code == 302
    assert "_auth_user_id" not in client.session


@pytest.mark.parametrize("identificador", ["ana.google", "ANA@GMAIL.COM"])
def test_login_tradicional_sigue_funcionando(client, usuario, identificador):
    google(client)
    assert client.post("/login/", {"username": identificador, "password": PASSWORD}).status_code == 302
    assert client.session["usuario_id"] == str(usuario.id)
    assert client.session["rol"] == usuario.rol
    assert PENDIENTE not in client.session


def test_google_deshabilitado_conserva_login(client, settings, usuario):
    settings.FIREBASE_GOOGLE_ENABLED = False
    assert b'id="google-login"' not in client.get("/login/").content
    assert google(client).status_code == 503
    assert client.post("/login/", {"username": usuario.username, "password": PASSWORD}).status_code == 302


def test_usuario_django_inactivo_no_puede_entrar(client, usuario):
    vinculo(usuario)
    User.objects.create_user(username=usuario.username, is_active=False)
    assert google(client).status_code == 403
    assert "_auth_user_id" not in client.session


def test_fallo_sesion_revierte_vinculacion_nueva(client, usuario):
    User.objects.create_user(username=usuario.username, is_active=False)
    assert google(client).json()["redirect"] == "/login/google/vincular/"
    assert vincular(client).context["form"].errors
    assert not GoogleVinculoModel.objects.exists()


@pytest.mark.parametrize("activo,staff", [(False, False), (True, True)])
def test_usuario_tecnico_huerfano_no_transmite_privilegios(client, activo, staff):
    from hashlib import sha256

    username = "web." + sha256(identidad().email.encode()).hexdigest()[:26]
    User.objects.create_user(username=username, is_active=activo, is_staff=staff, is_superuser=staff)
    google(client)
    assert completar(client).context["form"].errors
    assert not UsuarioModel.objects.exists()
    assert not ClienteModel.objects.exists()
    assert not GoogleVinculoModel.objects.exists()


@pytest.mark.parametrize("datos", [{}, {"id_token": 1}, {"id_token": "x", "next": []}, []])
def test_solicitud_invalida(client, datos):
    assert client.post("/login/google/", datos, content_type="application/json").status_code == 400


def test_desactivacion_local_invalida_sesion_google(client, usuario):
    vinculo(usuario)
    assert google(client).status_code == 200
    usuario.activo = False
    usuario.save()
    assert client.get("/catalogo/").status_code == 302
    assert "_auth_user_id" not in client.session
