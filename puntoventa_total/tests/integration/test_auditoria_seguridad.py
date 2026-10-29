"""Regresiones de redireccion, propiedad de clientes y paginacion."""
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User

from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_login_no_redirige_a_dominio_externo(client):
    usuario = SimpleNamespace(username="qa_login", rol="CLIENTE", nombre_completo="QA", id=str(uuid.uuid4()))
    with patch("src.modules.identity.presentation.views.login_view.AutenticarUsuario") as caso:
        caso.return_value.ejecutar.return_value = usuario
        respuesta = client.post("/login/?next=https://example.invalid/", {"username": "qa_login", "password": "Prueba123!"})
    assert respuesta.status_code == 302
    assert not respuesta["Location"].startswith("https://example.invalid")


@pytest.fixture
def cliente_ajeno(db):
    return ClienteModel.objects.create(id=uuid.uuid4(), nombre="Cliente privado", email="privado@example.test", usuario_id=uuid.uuid4())


def test_perfil_rechaza_anonimo(client, cliente_ajeno):
    respuesta = client.get(f"/clientes/perfil/{cliente_ajeno.id}/")
    assert respuesta.status_code == 302
    assert "/login/" in respuesta["Location"]


def test_cliente_no_lee_perfil_ajeno(client, cliente_ajeno):
    client.force_login(User.objects.create_user(username="qa_otro"))
    sesion = client.session
    sesion["rol"] = "CLIENTE"
    sesion["usuario_id"] = str(uuid.uuid4())
    sesion.save()
    respuesta = client.get(f"/clientes/perfil/{cliente_ajeno.id}/")
    assert respuesta.status_code in (403, 404)


@pytest.mark.parametrize("pagina", ["abc", "0", "-1", "1.5"])
def test_listado_ventas_rechaza_paginacion_invalida(client, pagina):
    client.force_login(User.objects.create_user(username="qa_cajero"))
    sesion = client.session
    sesion["rol"] = "CAJERO"
    sesion.save()
    client.raise_request_exception = False
    respuesta = client.get("/pos/ventas/", {"pagina": pagina})
    assert respuesta.status_code == 400


@pytest.mark.parametrize("next_url", ["/catalogo/", "https://testserver/catalogo/"])
def test_login_conserva_destino_local(client, next_url):
    usuario = SimpleNamespace(username="qa_login", rol="CLIENTE", nombre_completo="QA", id=str(uuid.uuid4()))
    with patch("src.modules.identity.presentation.views.login_view.AutenticarUsuario") as caso:
        caso.return_value.ejecutar.return_value = usuario
        respuesta = client.post("/login/", {"username": "qa_login", "password": "Prueba123!"}, QUERY_STRING=f"next={next_url}")
    assert respuesta.status_code == 302
    assert respuesta["Location"] == next_url


@pytest.mark.parametrize("rol,propietario,permitido", [
    ("CLIENTE", True, True), ("CLIENTE", False, False),
    ("CAJERO", False, True), ("GERENTE", False, True),
    ("ADMINISTRADOR", False, True), ("ALMACENERO", False, False), ("", True, False),
])
def test_perfil_aplica_permisos_en_lectura_y_escritura(client, cliente_ajeno, rol, propietario, permitido):
    client.force_login(User.objects.create_user(username="qa_perfil"))
    sesion = client.session
    sesion["rol"] = rol
    sesion["usuario_id"] = str(cliente_ajeno.usuario_id if propietario else uuid.uuid4())
    sesion.save()
    url = f"/clientes/perfil/{cliente_ajeno.id}/"
    assert client.get(url).status_code == (200 if permitido else 403)
    respuesta = client.post(url, {"nombre": "Nombre actualizado", "email": "nuevo@example.test"})
    assert respuesta.status_code == (302 if permitido else 403)
    cliente_ajeno.refresh_from_db()
    assert cliente_ajeno.nombre == ("Nombre actualizado" if permitido else "Cliente privado")


def test_historial_ajeno_no_es_visible_para_cliente(client, cliente_ajeno):
    client.force_login(User.objects.create_user(username="qa_historial"))
    sesion = client.session
    sesion["rol"] = "CLIENTE"
    sesion.save()
    respuesta = client.get(f"/clientes/historial/{cliente_ajeno.id}/")
    assert respuesta.status_code == 403
    assert b"privado@example.test" not in respuesta.content
