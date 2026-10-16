"""Regresiones de integridad detectadas por la auditoría de inventario."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.exceptions.stock_exceptions import StockException
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository


def test_repetir_liberacion_preserva_otras_reservas():
    stock = Mock(spec=StockRepository)
    reservas = Mock(spec=ReservaRepository)
    existencia = Existencia(producto_id="p", cantidad=10, reservada=5)
    reserva = ReservaStock(producto_id="p", cantidad=3)
    stock.obtener.return_value = existencia
    reservas.buscar_por_id.return_value = reserva
    caso = LiberarReserva(stock, reservas)
    caso.ejecutar(str(reserva.id))
    caso.ejecutar(str(reserva.id))
    assert existencia.reservada == 2
    stock.guardar.assert_called_once_with(existencia)
    reservas.guardar.assert_called_once_with(reserva)


@pytest.mark.parametrize("tz", [None, timezone.utc, timezone(timedelta(hours=-5))])
def test_expiracion_y_extension_respetan_zona_horaria(tz):
    reserva = ReservaStock(producto_id="p", cantidad=1,
                           expira_en=datetime.now(tz) + timedelta(days=1))
    assert reserva.activa
    reserva.extender(30)
    assert reserva.expira_en.tzinfo == tz
    assert timedelta(minutes=29) < reserva.expira_en - datetime.now(tz) <= timedelta(minutes=30)
    reserva.expira_en = datetime.now(tz) - timedelta(seconds=1)
    assert reserva.expirada
    assert not reserva.activa


INVALIDAS = [0.5, Decimal("1.5"), True, False, "2", None, float("nan")]


@pytest.mark.parametrize("cantidad", INVALIDAS)
@pytest.mark.parametrize("metodo", ["aplicar_entrada", "aplicar_salida", "reservar", "liberar", "confirmar_reserva"])
def test_cantidad_no_entera_no_modifica_stock(cantidad, metodo):
    existencia = Existencia(producto_id="p", cantidad=10, reservada=3)
    with pytest.raises(StockException):
        getattr(existencia, metodo)(cantidad)
    assert (existencia.cantidad, existencia.reservada) == (10, 3)


@pytest.mark.parametrize("cantidad", INVALIDAS)
@pytest.mark.parametrize("campo", ["cantidad", "reservada"])
def test_existencia_rechaza_estado_inicial_no_entero(cantidad, campo):
    with pytest.raises(StockException):
        Existencia(producto_id="p", **{campo: cantidad})
