import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


def test_flujo_pedido_web(client):
    assert client.get("/pedidos/seguimiento/").status_code == 200
    assert client.get("/pedidos/carrito/").status_code == 302  # requiere login

