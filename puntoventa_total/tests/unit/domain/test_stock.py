"""Invariantes de existencia, lotes, reservas y politica PEPS."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.unit, pytest.mark.core, pytest.mark.fast, pytest.mark.inventario]


def test_entrada_incrementa_stock_y_disponible():
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(10)
    assert existencia.cantidad == 10 and existencia.disponible == 10


def test_salida_supera_disponible_lanza_error():
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(3)
    with pytest.raises(StockInsuficiente):
        existencia.aplicar_salida(5)


def test_reserva_no_permite_doble_compromiso():
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(5)
    existencia.reservar(4)
    assert existencia.disponible == 1
    with pytest.raises(StockInsuficiente):
        existencia.reservar(2)


def test_confirmar_reserva_convierte_en_salida():
    existencia = Existencia(producto_id="p1")
    existencia.aplicar_entrada(5)
    existencia.reservar(3)
    existencia.confirmar_reserva(3)
    assert existencia.cantidad == 2 and existencia.reservada == 0


def test_planificacion_peps_prefiere_vencimiento_mas_proximo():
    hoy = date.today()
    lote_viejo = Lote(producto_id="p1", numero_lote="L1", cantidad_inicial=5, cantidad_restante=5,
                      costo_unitario=Monto(Decimal("3")), fecha_vencimiento=hoy + timedelta(days=10))
    lote_nuevo = Lote(producto_id="p1", numero_lote="L2", cantidad_inicial=5, cantidad_restante=5,
                      costo_unitario=Monto(Decimal("3")), fecha_vencimiento=hoy + timedelta(days=100))
    plan = PoliticaStock.planificar_salida_peps([lote_nuevo, lote_viejo], 3)
    assert plan[0][0].numero_lote == "L1"


def test_reserva_expirada_no_esta_activa():
    reserva = ReservaStock(producto_id="p1", cantidad=1, referencia="PEDIDO:P1")
    reserva.expira_en = datetime.now() - timedelta(minutes=1)
    assert not reserva.activa

from datetime import datetime  # noqa: E402

