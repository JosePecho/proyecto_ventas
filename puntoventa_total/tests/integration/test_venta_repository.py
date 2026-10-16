import pytest

from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.infrastructure.factories import construir_venta_repository
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_guardar_y_recuperar_agregado_completo():
    repo = construir_venta_repository()
    agregado = VentaAggregate(venta=Venta(numero_ticket="TINT1", cajero_id="00000000-0000-0000-0000-000000000001"))
    agregado.agregar_producto("00000000-0000-0000-0000-0000000000aa", " Producto X", 2, Monto("5.00"))
    repo.guardar(agregado)

    recuperado = repo.buscar_por_numero_ticket("TINT1")
    assert recuperado is not None
    assert len(recuperado.lineas) == 1
    assert recuperado.venta.estado == EstadoVenta.BORRADOR


def test_siguiente_numero_ticket_es_unico():
    # El correlativo se reserva en una secuencia persistente, independiente del conteo.
    repo = construir_venta_repository()
    primero = repo.siguiente_numero_ticket()
    repo.guardar(
        VentaAggregate(
            venta=Venta(numero_ticket=primero, cajero_id="00000000-0000-0000-0000-000000000001")
        )
    )
    segundo = repo.siguiente_numero_ticket()
    assert primero != segundo
    assert int(segundo[-5:]) == int(primero[-5:]) + 1

