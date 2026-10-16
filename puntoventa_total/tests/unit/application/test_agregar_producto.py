"""Nivel 1 - aplicacion: caso de uso AgregarProducto.

Reglas: RN-02 (producto descontinuado no se vende), RN-04 (stock disponible
>= cantidad pedida) y validacion de venta inexistente.
"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.sales.application.use_cases.agregar_producto import AgregarProducto
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoDescontinuado
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _sut(stock_disponible: int = 10, descuento_promo: str = "0.00"):
    repo, inventario, promociones = MagicMock(), MagicMock(), MagicMock()
    inventario.stock_disponible.return_value = stock_disponible
    promociones.descuento_producto.return_value = Monto(Decimal(descuento_promo))
    repo.buscar_por_id.return_value = VentaAggregate(venta=Venta(numero_ticket="T200", cajero_id="c1"))
    return AgregarProducto(repo, inventario, promociones), repo, inventario, promociones


def test_agregar_producto_con_stock_suficiente_actualiza_totales(producto_faker):
    sut, repo, inventario, promociones = _sut()

    salida = sut.ejecutar("v1", producto_faker(venta="8.50"), cantidad=2)

    assert len(salida.lineas) == 1
    assert salida.total == 17.0
    inventario.stock_disponible.assert_called_once()
    promociones.descuento_producto.assert_called_once()
    repo.guardar.assert_called_once()


def test_stock_insuficiente_bloquea_el_producto(producto_faker):
    sut, repo, inventario, _ = _sut(stock_disponible=1)

    with pytest.raises(StockInsuficiente):
        sut.ejecutar("v1", producto_faker(), cantidad=2)

    inventario.stock_disponible.assert_called_once()
    repo.guardar.assert_not_called()


def test_producto_descontinuado_no_se_puede_vender(producto_faker):
    sut, repo, _, _ = _sut()
    producto = producto_faker()
    producto.descontinuar()  # RN-02

    with pytest.raises(ProductoDescontinuado):
        sut.ejecutar("v1", producto, cantidad=1)

    repo.guardar.assert_not_called()


def test_producto_que_no_pide_stock_no_consulta_inventario(producto_faker):
    sut, _, inventario, _ = _sut()
    producto = producto_faker()
    producto.requiere_stock = False

    sut.ejecutar("v1", producto, cantidad=5)

    inventario.stock_disponible.assert_not_called()


def test_objeto_que_no_es_producto_dominio_es_rechazado():
    sut, repo, _, _ = _sut()
    with pytest.raises(ValidationException):
        sut.ejecutar("v1", "no-soy-producto", cantidad=1)
    repo.guardar.assert_not_called()


def test_venta_inexistente_es_rechazada(producto_faker):
    sut, repo, _, _ = _sut()
    repo.buscar_por_id.return_value = None

    with pytest.raises(VentaNoEncontrada):
        sut.ejecutar("fantasma", producto_faker(), cantidad=1)


def test_promocion_de_linea_se_aplica_como_porcentaje(producto_faker):
    sut, _, _, promociones = _sut(descuento_promo="0.85")  # 10% de 8.50

    salida = sut.ejecutar("v1", producto_faker(venta="8.50"), cantidad=1)

    linea = sut._repo.buscar_por_id.return_value.lineas[0]
    assert linea.pct_descuento == Decimal("10.00")
    assert linea.descuento.valor == Decimal("0.85")
    assert salida.total == 7.65
