import time

import pytest

from src.modules.catalog.infrastructure.factories import construir_producto_repository

pytestmark = [pytest.mark.performance, pytest.mark.django_db]


def test_busqueda_por_codigo_barras_es_rapida():
    repo = construir_producto_repository()
    inicio = time.perf_counter()
    repo.buscar_por_codigo_barras("7750000000001")
    duracion = time.perf_counter() - inicio
    assert duracion < 0.2, f"La busqueda tomo {duracion:.3f}s (max 200ms)"

