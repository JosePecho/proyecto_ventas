"""Nivel 1 - aplicacion: caso de uso AplicarPromocion del POS (modulo sales).

No confundir con tests/unit/application/test_aplicar_promocion.py, que ejercita
CalcularDescuento del modulo promotions.

Reglas: RN-07 (tope 50%) y RN-15 (sin promocion vigente no hay descuento).
"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.sales.application.use_cases.aplicar_promocion import AplicarPromocion
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.exceptions.venta_exceptions import (
    VentaException,
    VentaNoEncontrada,
)
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _venta_borrador(subtotal: str = "20.00") -> VentaAggregate:
    agregado = VentaAggregate(venta=Venta(numero_ticket="T300", cajero_id="c1"))
    agregado.agregar_producto("p1", "Camiseta", 1, Monto(Decimal(subtotal)))
    agregado.calcular_totales()
    return agregado


def _sut(agregado, descuento_sugerido: str = "0.00"):
    repo, promociones = MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = agregado
    promociones.descuento_venta.return_value = Monto(Decimal(descuento_sugerido))
    return AplicarPromocion(repo, promociones), repo, promociones


def test_descuento_manual_se_aplica_y_recalcula_totales():
    sut, repo, promociones = _sut(_venta_borrador("20.00"))

    salida = sut.ejecutar("v1", pct_descuento=Decimal("25"))

    assert salida.descuento == 5.0
    assert salida.total == 15.0
    promociones.descuento_venta.assert_not_called()  # modo manual no consulta promos
    repo.guardar.assert_called_once()


def test_descuento_manual_mayor_al_tope_de_50_es_rechazado():
    sut, repo, _, = _sut(_venta_borrador())
    with pytest.raises(VentaException):
        sut.ejecutar("v1", pct_descuento=Decimal("60"))
    repo.guardar.assert_not_called()


def test_sin_promocion_sugerida_no_hay_descuento():
    sut, _, promociones = _sut(_venta_borrador(), descuento_sugerido="0.00")

    with pytest.raises(ValidationException):
        sut.ejecutar("v1", pct_descuento=None)
    promociones.descuento_venta.assert_called_once()


def test_promocion_sugerida_se_convierte_en_porcentaje():
    sut, _, promociones = _sut(_venta_borrador("20.00"), descuento_sugerido="3.00")

    salida = sut.ejecutar("v1", pct_descuento=None)

    promociones.descuento_venta.assert_called_once()
    assert salida.descuento == 3.0
    assert salida.total == 17.0


def test_promocion_sugerida_mayor_al_tope_de_50_es_rechazada():
    # 12.00 de 20.00 = 60% -> el agregado debe rechazarlo (RN-07)
    sut, repo, _ = _sut(_venta_borrador("20.00"), descuento_sugerido="12.00")

    with pytest.raises(VentaException):
        sut.ejecutar("v1", pct_descuento=None)
    repo.guardar.assert_not_called()


def test_venta_inexistente_es_rechazada():
    sut, repo, _ = _sut(None)
    with pytest.raises(VentaNoEncontrada):
        sut.ejecutar("fantasma", pct_descuento=Decimal("10"))
