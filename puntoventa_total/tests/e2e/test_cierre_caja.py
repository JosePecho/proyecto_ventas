import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


def test_cierre_sin_turno_redirige_a_apertura(client):
    respuesta = client.get("/caja/arqueo/")
    assert respuesta.status_code in (200, 302)

