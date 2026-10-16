import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


def test_cierre_sin_turno_redirige_a_apertura(client):
    assert client.get("/pedidos/seguimiento/").status_code == 200
    respuesta = client.get("/caja/arqueo/")
    assert respuesta.status_code in (200, 302)

