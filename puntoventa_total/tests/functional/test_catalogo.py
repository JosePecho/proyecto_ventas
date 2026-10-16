import pytest

pytestmark = [pytest.mark.functional, pytest.mark.django_db]


def test_catalogo_responde(client):
    respuesta = client.get("/catalogo/")
    assert respuesta.status_code == 200


def test_busqueda_por_termino(client):
    respuesta = client.get("/catalogo/", {"q": "arroz"})
    assert respuesta.status_code == 200

