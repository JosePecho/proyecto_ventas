"""Fixtures compartidas: datos de prueba, fakes y utilidades."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from src.shared.domain.value_objects.monto import Monto


@pytest.fixture
def monto_base() -> Monto:
    return Monto(Decimal("100.00"))


@pytest.fixture
def moneda() -> str:
    return "PEN"


@pytest.fixture
def producto_faker():
    """Construye un producto de dominio valido sin tocar la base de datos."""
    from src.modules.catalog.domain.entities.producto import Producto
    from src.modules.catalog.domain.value_objects.precio import Precio

    def _crear(nombre: str = "Arroz 1kg", costo: str = "5.00", venta: str = "8.50", codigo: str | None = None):
        return Producto(
            nombre=nombre,
            descripcion="Producto de prueba",
            codigo_barras=codigo or f"775{uuid.uuid4().int % 10**10:010d}",
            precio=Precio(costo=Monto(Decimal(costo)), venta=Monto(Decimal(venta))),
        )

    return _crear


@pytest.fixture
def usuario_repository():
    from src.modules.identity.infrastructure.factories import construir_repositorio

    return construir_repositorio()


@pytest.fixture
def cliente_ip() -> str:
    return "127.0.0.1"

