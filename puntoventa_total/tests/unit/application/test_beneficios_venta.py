from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.modules.sales.application.use_cases.preparar_beneficios import PrepararBeneficiosVenta
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.entities.pago import Pago
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def venta():
    agregado = VentaAggregate(Venta(numero_ticket="T-BENEFICIO", cajero_id="cajero"))
    agregado.agregar_producto("pan", "Pan", 2, Monto(10))
    agregado.calcular_totales()
    return agregado


def test_beneficio_se_aplica_antes_del_pago_sin_compuesto():
    agregado, puerto = venta(), Mock()
    puerto.descuento_venta.return_value = Monto(2)
    caso = PrepararBeneficiosVenta(Mock(), puerto)
    caso.aplicar(agregado)
    caso.aplicar(agregado)
    assert agregado.descuento_venta_pct == Decimal("10")
    assert agregado.venta.total == 18


def test_pago_iniciado_congela_el_beneficio():
    agregado, puerto = venta(), Mock()
    agregado.registrar_pago(Pago.efectivo(str(agregado.venta.id), Monto(1)))
    PrepararBeneficiosVenta(Mock(), puerto).aplicar(agregado)
    puerto.descuento_venta.assert_not_called()
    assert agregado.venta.total == 20


def test_beneficio_superior_al_subtotal_es_rechazado():
    agregado, puerto = venta(), Mock()
    puerto.descuento_venta.return_value = Monto(21)
    with pytest.raises(ValidationException):
        PrepararBeneficiosVenta(Mock(), puerto).aplicar(agregado)
    assert agregado.venta.total == 20
