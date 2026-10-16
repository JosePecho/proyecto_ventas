"""Dos reservas simultaneas no deben dejar stock negativo."""
import pytest

from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
from src.modules.inventory.infrastructure.factories import construir_stock_repository

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_doble_reserva_agota_el_stock_disponible():
    repo = construir_stock_repository()
    producto_id = "00000000-0000-0000-0000-0000000000cc"
    existencia = Existencia(producto_id=producto_id)
    existencia.aplicar_entrada(5)
    repo.guardar(existencia)

    existencia.reservar(3)
    repo.guardar(existencia)

    # segundo intento sobre el estado persistido
    recargada = repo.obtener(producto_id)
    with pytest.raises(StockInsuficiente):
        recargada.reservar(3)

