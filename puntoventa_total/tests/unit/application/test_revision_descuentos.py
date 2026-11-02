"""Importes exactos de promociones y fallos que no deben ocultarse al cajero."""
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from src.modules.sales.application.use_cases.agregar_producto import agregar_linea
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.infrastructure.adapters.promociones_adapter import PromocionesAdapter
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def test_importe_nx1_no_pierde_dinero_por_redondear_el_porcentaje(producto_faker):
    producto = producto_faker(costo="5000", venta="10000")
    agregado = VentaAggregate(venta=Venta(cajero_id="cajero"))
    promociones = Mock()
    promociones.descuento_producto.return_value = Monto("10000")
    agregar_linea(agregado, producto, 3, promociones)
    agregado.calcular_totales()
    assert agregado.lineas[0].descuento.valor == Decimal("10000.00")
    assert agregado.venta.total == 20000


def test_fallo_del_motor_no_se_convierte_en_descuento_cero():
    with patch("src.modules.promotions.infrastructure.factories.construir_promocion_repository"), patch(
        "src.modules.promotions.application.use_cases.calcular_descuento.CalcularDescuento"
    ) as motor:
        motor.return_value.por_producto.side_effect = RuntimeError("Motor no disponible")
        with pytest.raises(RuntimeError, match="Motor no disponible"):
            PromocionesAdapter().descuento_producto("producto", Monto("17"), 2)
