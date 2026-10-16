import pytest

pytestmark = [pytest.mark.functional, pytest.mark.django_db]


def test_seguimiento_publico_responde(client):
    respuesta = client.get("/pedidos/seguimiento/", {"numero": "PX"})
    assert respuesta.status_code == 200


def test_carrito_requiere_login(client):
    respuesta = client.get("/pedidos/carrito/")
    assert respuesta.status_code == 302

