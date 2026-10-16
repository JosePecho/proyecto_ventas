"""Repositorio de productos sobre base de datos real (pytest-django)."""
import pytest

from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.value_objects.precio import Precio
from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def _crear(nombre="Cafe 250g", codigo="7759999000011"):
    return Producto(
        nombre=nombre,
        descripcion="Cafe de prueba",
        codigo_barras=codigo,
        precio=Precio(costo=Monto("4.00"), venta=Monto("9.00")),
    )


def test_guardar_y_buscar_por_codigo_barras():
    repo = construir_producto_repository()
    producto = _crear()
    repo.guardar(producto)

    encontrado = repo.buscar_por_codigo_barras("7759999000011")
    assert encontrado is not None
    assert encontrado.nombre == "Cafe 250g"


def test_codigo_barras_duplicado_se_rechaza():
    from src.modules.catalog.domain.exceptions.producto_exceptions import CodigoBarrasDuplicado

    repo = construir_producto_repository()
    repo.guardar(_crear())
    with pytest.raises(CodigoBarrasDuplicado):
        repo.guardar(_crear(nombre="Duplicado"))


def test_busqueda_por_termino():
    repo = construir_producto_repository()
    repo.guardar(_crear(nombre="Leche entera", codigo="7759999000022"))
    resultados = repo.listar(termino="leche")
    assert any(p.nombre == "Leche entera" for p in resultados)

