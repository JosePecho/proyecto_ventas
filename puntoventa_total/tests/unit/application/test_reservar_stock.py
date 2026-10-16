from unittest.mock import MagicMock

import pytest

from src.modules.inventory.application.use_cases.reservar_stock import ReservarStock
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente

pytestmark = pytest.mark.unit


def test_reserva_acota_disponible_sin_descontar_fisico():
    stock_repo, reserva_repo = MagicMock(), MagicMock()
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(10)
    stock_repo.obtener.return_value = existencia

    reserva_id = ReservarStock(stock_repo, reserva_repo).ejecutar("p1", 4, "PEDIDO:P1")

    assert reserva_id
    assert existencia.cantidad == 10
    assert existencia.disponible == 6
    reserva_repo.guardar.assert_called_once()


def test_reserva_sin_stock_lanza_error():
    stock_repo, reserva_repo = MagicMock(), MagicMock()
    stock_repo.obtener.return_value = None
    with pytest.raises(StockInsuficiente):
        ReservarStock(stock_repo, reserva_repo).ejecutar("p1", 1, "PEDIDO:P1")

