import pytest

pytestmark = [pytest.mark.functional, pytest.mark.django_db]


def test_pos_redirige_si_no_autenticado(client):
    respuesta = client.get("/pos/", follow=False)
    assert respuesta.status_code == 302
    assert "/login/" in respuesta["Location"]


def test_busqueda_pos_requiere_sesion(client):
    respuesta = client.get("/pos/buscar/?q=775")
    assert respuesta.status_code == 302

