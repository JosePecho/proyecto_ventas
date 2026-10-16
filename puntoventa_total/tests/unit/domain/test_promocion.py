from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.enums.estado_promocion import EstadoPromocion
from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _promocion_porcentaje(pct: int = 20) -> Promocion:
    promo = Promocion(
        nombre="20% off",
        tipo=TipoPromocion.PORCENTAJE,
        producto_id="p1",
        descuento=Descuento.porcentaje(Decimal(pct)),
    )
    promo.activar()
    return promo


def test_promocion_vigente_aplica_descuento():
    promo = _promocion_porcentaje(20)
    descuento = promo.calcular_descuento(Monto(Decimal("50.00")))
    assert descuento.valor == Decimal("10.00")


def test_promocion_fuera_de_vigencia_no_aplica():
    promo = _promocion_porcentaje()
    promo.vigencia_desde = datetime.now() + timedelta(days=1)
    promo.vigencia_hasta = datetime.now() + timedelta(days=2)
    assert not promo.esta_vigente()
    assert promo.calcular_descuento(Monto(Decimal("50.00"))).valor == 0


def test_promocion_2x1_entrega_unidad_gratuita():
    promo = Promocion(
        nombre="3x2",
        tipo=TipoPromocion.NX1,
        producto_id="p1",
        descuento=Descuento.porcentaje(Decimal("10")),
        cantidad_requerida=3,
        cantidad_gratuita=1,
    )
    promo.activar()
    descuento = promo.calcular_descuento(Monto(Decimal("30.00")), cantidad=3)
    assert descuento.valor == Decimal("10.00")


def test_promocion_cancelada_no_puede_activarse():
    from src.modules.promotions.domain.exceptions.promocion_exceptions import PromocionException

    promo = _promocion_porcentaje()
    promo.cancelar()
    with pytest.raises(PromocionException):
        promo.activar()

