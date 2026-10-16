"""Nivel 1: reglas reales de inventario sin ORM, red ni broker."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from hypothesis import given, settings, strategies as st

from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
from src.modules.inventory.application.dto.stock_dto import AjusteStockDTO
from src.modules.inventory.application.use_cases.ajustar_stock import AjustarStock
from src.modules.inventory.application.use_cases.alertar_stock_minimo import AlertarStockMinimo
from src.modules.inventory.application.use_cases.alertar_vencimientos import AlertarVencimientos
from src.modules.inventory.application.use_cases.confirmar_salida_reservada import ConfirmarSalidaReservada
from src.modules.inventory.application.use_cases.consultar_kardex import ConsultarKardex
from src.modules.inventory.application.use_cases.consultar_lotes import ConsultarLotes
from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
from src.modules.inventory.application.use_cases.descontar_stock import DescontarStock
from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
from src.modules.inventory.application.use_cases.registrar_merma import RegistrarMerma
from src.modules.inventory.application.use_cases.reservar_stock import ReservarStock
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.exceptions.stock_exceptions import (
    ExistenciaNegativa, LoteNoEncontrado, ReservaNoEncontrada, ReservaYaConfirmada,
    StockException, StockInsuficiente,
)
from src.modules.inventory.domain.repositories.lote_repository import LoteRepository
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit
HOY = date(2026, 10, 16)


@pytest.fixture(autouse=True)
def reloj_fijo(monkeypatch):
    class FechaFija(date):
        @classmethod
        def today(cls):
            return HOY

    class InstanteFijo(datetime):
        @classmethod
        def now(cls, tz=None):
            instante = datetime(2026, 10, 16, 12)
            return instante if tz is None else instante.replace(tzinfo=tz)

    monkeypatch.setattr("src.modules.inventory.domain.entities.lote.date", FechaFija)
    monkeypatch.setattr("src.modules.inventory.domain.entities.reserva_stock.datetime", InstanteFijo)
    monkeypatch.setattr("src.modules.inventory.domain.services.politica_stock.date", FechaFija)


def lote(cantidad=10, dias=10, producto="p1"):
    return Lote(producto_id=producto, numero_lote="L-UNIT", cantidad_inicial=cantidad,
                cantidad_restante=cantidad, costo_unitario=Monto(5),
                fecha_vencimiento=HOY + timedelta(days=dias))


@pytest.fixture
def puertos():
    stock = Mock(spec=StockRepository)
    stock.obtener.return_value = Existencia(producto_id="p1", cantidad=10)
    stock.umbral_minimo.return_value = 5
    lotes = Mock(spec=LoteRepository)
    lotes.listar_por_producto.return_value = [lote()]
    lotes.buscar_por_id.return_value = lote()
    movimientos = Mock(spec=MovimientoRepository)
    reservas = Mock(spec=ReservaRepository)
    reservas.buscar_por_id.return_value = ReservaStock(producto_id="p1", cantidad=2, referencia="PEDIDO:1")
    return SimpleNamespace(stock=stock, lotes=lotes, mov=movimientos, reservas=reservas)


@settings(max_examples=75, derandomize=True, deadline=None)
@given(inicial=st.integers(0, 10000), entrada=st.integers(1, 1000), salida=st.integers(1, 1000))
def test_propiedad_stock_se_conserva_y_nunca_es_negativo(inicial, entrada, salida):
    existencia = Existencia(producto_id="p1", cantidad=inicial)
    existencia.aplicar_entrada(entrada)
    antes = existencia.cantidad
    if salida > antes:
        with pytest.raises(StockInsuficiente):
            existencia.aplicar_salida(salida)
        assert existencia.cantidad == antes
    else:
        existencia.aplicar_salida(salida)
        assert existencia.cantidad == inicial + entrada - salida
    assert 0 <= existencia.reservada <= existencia.cantidad


@pytest.mark.parametrize("cantidad,reservada", [(-1, 0), (0, -1), (2, 3)])
def test_existencia_rechaza_estado_imposible(cantidad, reservada):
    with pytest.raises(ExistenciaNegativa):
        Existencia(producto_id="p1", cantidad=cantidad, reservada=reservada)


@pytest.mark.parametrize("metodo", ["aplicar_entrada", "aplicar_salida", "reservar", "liberar", "confirmar_reserva"])
@pytest.mark.parametrize("cantidad", [0, -1])
def test_cantidades_no_positivas_rechazadas(metodo, cantidad):
    with pytest.raises(StockException):
        getattr(Existencia(producto_id="p1", cantidad=10), metodo)(cantidad)


def test_reserva_libera_y_confirma_sin_alterar_disponible_indebidamente():
    existencia = Existencia(producto_id="p1", cantidad=10)
    existencia.reservar(4)
    existencia.liberar(1)
    assert existencia.disponible == 7
    existencia.confirmar_reserva(3)
    assert (existencia.cantidad, existencia.reservada, existencia.disponible) == (7, 0, 7)
    assert not existencia.con_stock_minimo(7)
    assert existencia.con_stock_minimo(8)
    with pytest.raises(StockInsuficiente):
        existencia.confirmar_reserva(1)


def test_peps_distribuye_y_omite_lotes_vencidos_sin_mutarlos():
    vencido, cercano, lejano = lote(10, -1), lote(3, 1), lote(9, 20)
    plan = PoliticaStock.planificar_salida_peps([lejano, vencido, cercano], 5)
    assert plan == [(cercano, 3), (lejano, 2)]
    assert [l.cantidad_restante for l in (vencido, cercano, lejano)] == [10, 3, 9]
    with pytest.raises(StockInsuficiente):
        PoliticaStock.planificar_salida_peps([vencido], 1)


@pytest.mark.parametrize("dias,esperado", [(-1, False), (0, True), (30, True), (31, False)])
def test_limites_alerta_vencimiento(dias, esperado):
    assert PoliticaStock.requiere_alerta_vencimiento(lote(dias=dias)) == esperado


def test_lote_valida_cantidad_y_agotamiento():
    with pytest.raises(ValidationException):
        lote(0)
    l = lote(2)
    with pytest.raises(ValidationException):
        l.descontar(0)
    with pytest.raises(StockInsuficiente):
        l.descontar(3)
    l.descontar(2)
    assert l.agotado
    l.fecha_vencimiento = None
    assert l.dias_para_vencer is None and not l.vencido()
    l.cantidad_restante = 3
    with pytest.raises(ValidationException):
        l.__post_init__()


def test_movimiento_signo_y_validaciones():
    entrada = MovimientoStock(producto_id="p1", tipo="ENTRADA", cantidad=2, stock_resultante=2)
    salida = MovimientoStock(producto_id="p1", tipo="MERMA", cantidad=1, stock_resultante=1)
    assert entrada.signo() == 1 and salida.signo() == -1
    with pytest.raises(ValidationException):
        MovimientoStock(producto_id="p1", cantidad=0)
    with pytest.raises(ValidationException):
        MovimientoStock(producto_id="p1", cantidad=1, stock_resultante=-1)
    assert TipoMovimiento.MERMA in PoliticaStock.tipos_que_descuentan()


def test_reserva_estados_y_expiracion():
    r = ReservaStock(producto_id="p1", cantidad=2, referencia="P:1")
    assert r.activa
    r.extender(30)
    r.confirmar()
    with pytest.raises(ReservaYaConfirmada):
        r.confirmar()
    with pytest.raises(ReservaYaConfirmada):
        r.liberar()
    with pytest.raises(ReservaYaConfirmada):
        r.extender()
    vencida = ReservaStock(producto_id="p1", cantidad=1, expira_en=datetime(2026, 10, 15))
    assert vencida.expirada and not vencida.activa
    with pytest.raises(ValidationException):
        ReservaStock(producto_id="p1", cantidad=0)


@pytest.mark.parametrize("fecha", [HOY, HOY.isoformat(), None])
def test_recibir_crea_lote_existencia_y_kardex(puertos, fecha):
    puertos.stock.obtener.return_value = None
    dto = RecepcionLoteDTO("p1", "L-UNIT", 4, 5, fecha_vencimiento=fecha)
    resultado = RecibirMercaderia(puertos.stock, puertos.lotes, puertos.mov).ejecutar(dto)
    assert resultado.cantidad_restante == 4
    assert puertos.stock.guardar.call_args.args[0].cantidad == 4
    assert puertos.mov.guardar.call_args.args[0].tipo == TipoMovimiento.ENTRADA


def test_descontar_distribuye_salidas_y_usa_uow(puertos):
    uow = Mock()
    uow.__enter__ = Mock(return_value=uow)
    uow.__exit__ = Mock(return_value=False)
    assert DescontarStock(puertos.stock, puertos.lotes, puertos.mov, uow=uow).ejecutar("p1", 3) == 7
    uow.__enter__.assert_called_once()
    uow.__exit__.assert_called_once_with(None, None, None)
    salida = puertos.mov.guardar.call_args.args[0]
    assert salida.cantidad == 3 and salida.stock_resultante == 7 and salida.lote_id


def test_descontar_sin_existencia_no_guarda(puertos):
    puertos.stock.obtener.return_value = None
    with pytest.raises(StockInsuficiente):
        DescontarStock(puertos.stock, puertos.lotes, puertos.mov).ejecutar("p1", 1)
    puertos.mov.guardar.assert_not_called()


@pytest.mark.parametrize("motivo", ["VENCIDO", "DANADO", "ROBO"])
def test_merma_con_motivo_y_lote(puertos, motivo):
    caso = RegistrarMerma(puertos.stock, puertos.lotes, puertos.mov)
    assert caso.ejecutar("p1", 2, motivo, "u1", lote_id="l1") == 8
    assert puertos.mov.guardar.call_args.args[0].referencia == f"MERMA:{motivo}"


@pytest.mark.parametrize("fallo", ["motivo", "sin_stock", "sin_lote", "otro_producto", "exceso_lote", "sin_cobertura"])
def test_merma_invalida_no_persiste(puertos, fallo):
    motivo, lote_id = "ROBO", "l1"
    if fallo == "motivo":
        motivo = "INVALIDO"
    elif fallo == "sin_stock":
        puertos.stock.obtener.return_value = None
    elif fallo == "sin_lote":
        puertos.lotes.buscar_por_id.return_value = None
    elif fallo == "otro_producto":
        puertos.lotes.buscar_por_id.return_value = lote(producto="p2")
    elif fallo == "exceso_lote":
        puertos.lotes.buscar_por_id.return_value = lote(1)
    else:
        lote_id = None
        puertos.lotes.listar_por_producto.return_value = [lote(1)]
    with pytest.raises((ValidationException, LoteNoEncontrado)):
        RegistrarMerma(puertos.stock, puertos.lotes, puertos.mov).ejecutar("p1", 2, motivo, "u1", lote_id=lote_id)
    puertos.stock.guardar.assert_not_called()
    puertos.lotes.guardar.assert_not_called()
    puertos.mov.guardar.assert_not_called()


def test_merma_sin_lote_incluye_vencidos(puertos):
    puertos.lotes.listar_por_producto.return_value = [lote(2, -1), lote(8, 10)]
    assert RegistrarMerma(puertos.stock, puertos.lotes, puertos.mov).ejecutar("p1", 3, "VENCIDO", "u1") == 7
    assert puertos.lotes.guardar.call_count == 2


@pytest.mark.parametrize("cantidad,tipo", [(2, TipoMovimiento.AJUSTE_POSITIVO), (-2, TipoMovimiento.AJUSTE_NEGATIVO)])
def test_ajustar_stock_guarda_diferencia_absoluta(puertos, cantidad, tipo):
    assert AjustarStock(puertos.stock, puertos.mov).ejecutar(AjusteStockDTO("p1", cantidad, "u1")) == 10 + cantidad
    movimiento = puertos.mov.guardar.call_args.args[0]
    assert movimiento.tipo == tipo and movimiento.cantidad == 2


def test_ajuste_cero_rechazado(puertos):
    with pytest.raises(ValidationException):
        AjustarStock(puertos.stock, puertos.mov).ejecutar(AjusteStockDTO("p1", 0, "u1"))


def test_reservar_y_liberar(puertos):
    reserva_id = ReservarStock(puertos.stock, puertos.reservas).ejecutar("p1", 2, "P:1")
    assert reserva_id and puertos.stock.obtener.return_value.reservada == 2
    LiberarReserva(puertos.stock, puertos.reservas).ejecutar(reserva_id)
    assert puertos.stock.obtener.return_value.reservada == 0


@pytest.mark.parametrize("operacion", ["reservar", "liberar", "confirmar"])
def test_reservas_ausentes_rechazadas(puertos, operacion):
    puertos.stock.obtener.return_value = None
    puertos.reservas.buscar_por_id.return_value = None
    with pytest.raises((ReservaNoEncontrada, StockInsuficiente)):
        if operacion == "reservar":
            ReservarStock(puertos.stock, puertos.reservas).ejecutar("p1", 1, "P:1")
        elif operacion == "liberar":
            LiberarReserva(puertos.stock, puertos.reservas).ejecutar("r1")
        else:
            ConfirmarSalidaReservada(puertos.stock, puertos.reservas, puertos.mov).ejecutar("r1")


def test_liberar_confirmada_rechaza_y_expiradas_se_procesan(puertos):
    puertos.reservas.buscar_por_id.return_value.confirmar()
    with pytest.raises(ReservaYaConfirmada):
        LiberarReserva(puertos.stock, puertos.reservas).ejecutar("r1")
    r = ReservaStock(producto_id="p1", cantidad=1)
    puertos.reservas.buscar_por_id.return_value = r
    puertos.reservas.listar_activas_expiradas.return_value = [r]
    puertos.stock.obtener.return_value.reservada = 1
    assert LiberarReserva(puertos.stock, puertos.reservas).liberar_expiradas() == 1


def test_confirmar_reserva_descuenta_lotes(puertos):
    puertos.stock.obtener.return_value.reservada = 2
    caso = ConfirmarSalidaReservada(puertos.stock, puertos.reservas, puertos.mov, lote_repo=puertos.lotes)
    assert caso.ejecutar("r1", "PEDIDO:1") == 8
    assert puertos.lotes.guardar.call_args.args[0].cantidad_restante == 8


def test_alertas_usan_minimo_individual_y_notificador(puertos):
    notificador = Mock()
    puertos.stock.productos_bajo_minimo.return_value = [{"producto_id": "p1", "disponible": 3, "stock_minimo": 8}]
    assert AlertarStockMinimo(puertos.stock, notificador).ejecutar() == 1
    notificador.notificar_stock_minimo.assert_called_once_with("p1", 3, 8)
    puertos.lotes.lotes_por_vencer.return_value = [lote(dias=0)]
    assert AlertarVencimientos(puertos.lotes, notificador).ejecutar() == 1
    assert notificador.notificar_vencimiento.call_args.args[2] == 0


def test_consultas_stock_lotes_y_kardex(puertos):
    assert ConsultarStock(puertos.stock).ejecutar("p1").disponible == 10
    puertos.stock.obtener.return_value = None
    assert ConsultarStock(puertos.stock).ejecutar("p1").bajo_minimo
    puertos.lotes.lotes_vencidos.return_value = [lote(dias=-1)]
    assert len(ConsultarLotes(puertos.lotes).ejecutar("p1")) == 1
    assert ConsultarLotes(puertos.lotes).ejecutar_vencidos()[0].vencido
    puertos.mov.kardex.return_value = [MovimientoStock(producto_id="p1", cantidad=1, stock_resultante=1)]
    puertos.mov.contar_kardex.return_value = 1
    assert ConsultarKardex(puertos.mov).ejecutar("p1", "2026-10-01", "2026-10-16").total == 1


@pytest.mark.parametrize("kwargs", [{"pagina": 0}, {"por_pagina": 0}, {"desde": "x"},
                                   {"desde": "2026-10-16", "hasta": "2026-10-01"}])
def test_kardex_valida_filtros(puertos, kwargs):
    with pytest.raises(ValueError):
        ConsultarKardex(puertos.mov).ejecutar("p1", **kwargs)
