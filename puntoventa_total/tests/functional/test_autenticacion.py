import pytest

pytestmark = [pytest.mark.functional, pytest.mark.django_db]


def test_login_requiere_credenciales(client):
    respuesta = client.get("/login/")
    assert respuesta.status_code == 200
    assert b"form" in respuesta.content


def test_logout_redirige_al_login(client):
    assert client.get("/logout/").status_code == 405
    respuesta = client.post("/logout/", follow=True)
    assert respuesta.status_code == 200

