"""La venta solo debe descontar stock si el cobro se completa."""
from decimal import Decimal

import pytest

from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.infrastructure.factories import construir_stock_repository
from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.infrastructure.factories import construir_auditoria_port, construir_inventario_port
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_stock_no_descuenta_con_pago_parcial():
    stock_repo = construir_stock_repository()
    producto_id = "00000000-0000-0000-0000-0000000000bb"
    existencia = Existencia(producto_id=producto_id)
    existencia.aplicar_entrada(10)
    stock_repo.guardar(existencia)

    agregado = VentaAggregate(venta=Venta(numero_ticket="TSTOCK", cajero_id="00000000-0000-0000-0000-000000000001"))
    agregado.agregar_producto(producto_id, "Item", 3, Monto(Decimal("10.00")))
    agregado.calcular_totales()

    class RepoFake:
        def buscar_por_id(self, _):
            return agregado

        def guardar(self, a):
            return a

    ProcesarPago(RepoFake(), construir_inventario_port(), construir_auditoria_port()).ejecutar(
        ProcesarPagoDTO(venta_id="v", metodo="EFECTIVO", monto=5.0)
    )
    assert ConsultarStock(stock_repo).ejecutar(producto_id).disponible == 10

