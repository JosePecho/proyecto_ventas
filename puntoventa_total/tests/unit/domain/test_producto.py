"""Reglas de negocio del producto: precios, margen y descontinuacion."""
from decimal import Decimal

import pytest

from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.enums.estado_producto import EstadoProducto
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoDescontinuado
from src.modules.catalog.domain.value_objects.precio import Precio
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def test_producto_se_crea_con_precio_valido(producto_faker):
    producto = producto_faker()
    assert producto.precio_venta.valor == Decimal("8.50")
    assert producto.disponible_para_vender


def test_producto_rechaza_precio_debajo_del_costo():
    with pytest.raises(ValidationException):
        Precio(costo=Monto(Decimal("10.00")), venta=Monto(Decimal("5.00")))


def test_producto_rechaza_nombre_vacio():
    with pytest.raises(ValidationException):
        Producto(
            nombre="  ",
            codigo_barras="7751234567890",
            precio=Precio(costo=Monto(Decimal("1")), venta=Monto(Decimal("2"))),
        )


def test_descontinuar_bloquea_venta(producto_faker):
    producto = producto_faker()
    producto.descontinuar("fin de linea")
    assert producto.estado == EstadoProducto.DESCONTINUADO
    with pytest.raises(ProductoDescontinuado):
        producto.verificar_disponibilidad_venta()


def test_margen_minimo_se_respeta():
    with pytest.raises(ValidationException):
        Precio(costo=Monto(Decimal("100")), venta=Monto(Decimal("101")))

