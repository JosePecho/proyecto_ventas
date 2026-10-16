from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.promotions.application.use_cases.calcular_descuento import CalcularDescuento
from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _promocion_activa(pct: int) -> Promocion:
    promo = Promocion(
        nombre=f"{pct}% ",
        tipo=TipoPromocion.PORCENTAJE,
        producto_id="p1",
        descuento=Descuento.porcentaje(Decimal(pct)),
    )
    promo.activar()
    return promo


def test_descuento_selecciona_la_mejor_promocion():
    repo = MagicMock()
    repo.listar_activas.return_value = [_promocion_activa(10), _promocion_activa(25)]

    descuento = CalcularDescuento(repo).por_producto("p1", Monto(Decimal("100.00")), cantidad=1)

    assert descuento.valor == Decimal("25.00")


def test_sin_promociones_devuelve_cero():
    repo = MagicMock()
    repo.listar_activas.return_value = []

    descuento = CalcularDescuento(repo).por_producto("p1", Monto(Decimal("100.00")))
    assert descuento.valor == 0

