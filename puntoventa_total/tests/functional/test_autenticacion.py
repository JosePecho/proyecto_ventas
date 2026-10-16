import pytest

pytestmark = [pytest.mark.functional, pytest.mark.django_db]


def test_login_requiere_credenciales(client):
    respuesta = client.get("/login/")
    assert respuesta.status_code == 200
    assert b"form" in respuesta.content


def test_logout_redirige_al_login(client):
    respuesta = client.get("/logout/", follow=True)
    assert respuesta.status_code == 200

