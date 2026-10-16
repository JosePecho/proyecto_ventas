import time

import pytest

from src.modules.catalog.infrastructure.factories import construir_producto_repository

pytestmark = [pytest.mark.performance, pytest.mark.django_db]


def test_listado_responde_bajo_demanda():
    repo = construir_producto_repository()
    inicio = time.perf_counter()
    repo.listar(limit=20)
    duracion = time.perf_counter() - inicio
    assert duracion < 0.5, f"El listado tomo {duracion:.3f}s (max 500ms)"
