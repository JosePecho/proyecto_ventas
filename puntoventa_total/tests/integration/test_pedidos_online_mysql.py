"""Dos solicitudes simultáneas al mismo pedido: InnoDB sin dobles reservas."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, close_old_connections, connections, transaction

from tests.integration.test_pedidos_online import carrito
from src.modules.orders.application.use_cases.confirmar_pedido import ConfirmarPedido
from src.modules.orders.application.use_cases.cancelar_pedido import CancelarPedido
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.modules.orders.infrastructure.factories import construir_inventario_port, construir_pedido_repository
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel
from src.modules.inventory.infrastructure.persistence.django_models.reserva_model import ReservaModel

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True),
              pytest.mark.skipif(connection.vendor != "mysql", reason="Requiere MySQL/InnoDB real")]


@pytest.mark.parametrize("accion", ["confirmar", "cancelar"])
def test_dos_escritores_sobre_un_pedido(client, accion):
    pedido, producto = carrito(client)
    if accion == "cancelar":
        ConfirmarPedido(construir_pedido_repository(), construir_inventario_port(), uow=transaction.atomic()).ejecutar(str(pedido.id))
    barrera = Barrier(2, timeout=10)

    def ejecutar():
        close_old_connections()
        try:
            barrera.wait()
            caso = ConfirmarPedido if accion == "confirmar" else CancelarPedido
            caso(construir_pedido_repository(), construir_inventario_port(), uow=transaction.atomic()).ejecutar(str(pedido.id))
            return "aceptado"
        except PedidoException:
            return "rechazado"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(ejecutar) for _ in range(2)]
        assert sorted(f.result(timeout=25) for f in futuros) == ["aceptado", "rechazado"]
    pedido.refresh_from_db()
    assert pedido.estado == ("CONFIRMADO" if accion == "confirmar" else "CANCELADO")
    stock = ExistenciaModel.objects.get(producto_id=producto.id)
    assert stock.cantidad == 10
    assert stock.reservada == (2 if accion == "confirmar" else 0)
    assert ReservaModel.objects.filter(referencia=f"PEDIDO:{pedido.numero}").count() == 1
