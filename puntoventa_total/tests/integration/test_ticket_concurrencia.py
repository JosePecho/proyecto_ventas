from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection, connections

from src.modules.sales.infrastructure.factories import construir_venta_repository

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True)]


def test_correlativo_reservado_no_se_reutiliza_sin_guardar_venta():
    repo = construir_venta_repository()
    primero, segundo = repo.siguiente_numero_ticket(), repo.siguiente_numero_ticket()
    assert primero != segundo
    assert int(segundo[9:]) == int(primero[9:]) + 1


@pytest.mark.skipif(connection.vendor != "mysql", reason="Requiere bloqueo de fila InnoDB")
def test_ocho_cajas_reservan_tickets_distintos_simultaneamente():
    barrera = Barrier(8, timeout=10)

    def reservar(_):
        close_old_connections()
        try:
            barrera.wait()
            return construir_venta_repository().siguiente_numero_ticket()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=8) as pool:
        numeros = list(pool.map(reservar, range(8)))
    assert len(set(numeros)) == 8
    assert sorted(int(n[9:]) for n in numeros) == list(range(1, 9))
