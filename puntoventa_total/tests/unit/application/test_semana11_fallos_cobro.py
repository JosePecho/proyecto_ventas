"""Rutas excepcionales, orden observable y pagos sucesivos del cobro."""
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaException, VentaNoModificable
from src.shared.application.interfaces.unit_of_work import UnitOfWork
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


@pytest.fixture
def entorno():
    agregado = VentaAggregate(Venta(numero_ticket="S11-FALLOS", cajero_id="cajero"))
    agregado.agregar_producto("p1", "Arroz", 1, Monto(10))
    agregado.agregar_producto("p2", "Aceite", 1, Monto(10))
    agregado.calcular_totales()
    repo, inventario, auditoria = Mock(), Mock(), Mock()
    repo.buscar_por_id.return_value = agregado
    uow = MagicMock(spec=UnitOfWork)
    uow.__exit__.return_value = False
    return agregado, repo, inventario, auditoria, uow


def dto(monto=20):
    return ProcesarPagoDTO("venta", "EFECTIVO", monto, monto)


@pytest.mark.parametrize("estado", [EstadoVenta.PAGADA, EstadoVenta.ANULADA])
def test_venta_cerrada_no_admite_otro_pago(entorno, estado):
    agregado, repo, inventario, auditoria, uow = entorno
    agregado.venta.estado = estado
    with pytest.raises(VentaNoModificable) as error:
        ProcesarPago(repo, inventario, auditoria, uow).ejecutar(dto())
    assert agregado.pagos == []
    repo.guardar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()
    assert uow.__exit__.call_args.args[:2] == (VentaNoModificable, error.value)


@pytest.mark.parametrize("etapa", ["buscar", "promociones", "inventario", "cerrar", "guardar", "auditar"])
def test_propaga_fallo_y_entrega_excepcion_al_uow(entorno, etapa):
    agregado, repo, inventario, auditoria, uow = entorno
    fallo = RuntimeError(f"Fallo controlado: {etapa}")
    with patch("src.modules.sales.application.use_cases.preparar_beneficios.PrepararBeneficiosVenta") as preparar:
        if etapa == "buscar":
            repo.buscar_por_id.side_effect = fallo
        elif etapa == "promociones":
            preparar.return_value.aplicar.side_effect = fallo
        elif etapa == "inventario":
            inventario.descontar.side_effect = [None, fallo]
        elif etapa == "cerrar":
            agregado.cerrar = Mock(side_effect=fallo)
        elif etapa == "guardar":
            repo.guardar.side_effect = fallo
        else:
            auditoria.registrar.side_effect = fallo
        with pytest.raises(RuntimeError) as error:
            ProcesarPago(repo, inventario, auditoria, uow, promociones=Mock()).ejecutar(dto())
    assert error.value is fallo
    uow.__enter__.assert_called_once_with()
    tipo, excepcion, traceback = uow.__exit__.call_args.args
    assert tipo is RuntimeError and excepcion is fallo and traceback is not None
    if etapa in ("buscar", "promociones"):
        assert agregado.pagos == []
        inventario.descontar.assert_not_called()
    if etapa in ("buscar", "promociones", "inventario", "cerrar"):
        repo.guardar.assert_not_called()
    if etapa != "auditar":
        auditoria.registrar.assert_not_called()
    if etapa == "inventario":
        assert agregado.venta.estado is EstadoVenta.BORRADOR
        assert inventario.descontar.call_count == 2


def test_orden_de_operaciones_exacto(entorno):
    agregado, repo, inventario, auditoria, uow = entorno
    eventos = []
    uow.__enter__.side_effect = lambda: eventos.append("entrar")
    uow.__exit__.side_effect = lambda *args: eventos.append("salir")
    repo.buscar_por_id.side_effect = lambda _: eventos.append("buscar") or agregado
    verificar, registrar, cerrar = agregado.venta.verificar_modificable, agregado.registrar_pago, agregado.cerrar
    agregado.venta.verificar_modificable = Mock(side_effect=lambda: (eventos.append("verificar"), verificar())[1])
    agregado.registrar_pago = Mock(side_effect=lambda pago: (eventos.append("pago"), registrar(pago))[1])
    agregado.cerrar = Mock(side_effect=lambda: (eventos.append("cerrar"), cerrar())[1])
    inventario.descontar.side_effect = lambda producto, *args: eventos.append(f"stock:{producto}")
    repo.guardar.side_effect = lambda _: eventos.append("guardar")
    auditoria.registrar.side_effect = lambda **kwargs: eventos.append("auditar")
    with patch("src.modules.sales.application.use_cases.preparar_beneficios.PrepararBeneficiosVenta") as preparar:
        preparar.return_value.aplicar.side_effect = lambda _: eventos.append("promociones")
        ProcesarPago(repo, inventario, auditoria, uow, promociones=Mock()).ejecutar(dto())
    assert eventos == ["entrar", "buscar", "verificar", "promociones", "pago", "stock:p1", "stock:p2",
                       "cerrar", "guardar", "auditar", "salir"]


def test_dos_pagos_reales_cierran_y_descuentan_una_sola_vez(entorno):
    agregado, repo, inventario, auditoria, uow = entorno
    caso = ProcesarPago(repo, inventario, auditoria, uow)
    assert caso.ejecutar(dto(7)) == {"estado": "PENDIENTE", "saldo": 13.0}
    assert agregado.venta.estado is EstadoVenta.BORRADOR
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()
    resultado = caso.ejecutar(dto(13))
    assert resultado["estado"] == "PAGADA"
    assert agregado.total_pagado() == Monto(20).valor
    assert agregado.saldo_pendiente() == 0
    assert len(agregado.pagos) == 2
    assert inventario.descontar.call_count == 2  # una llamada por cada producto
    auditoria.registrar.assert_called_once()
    assert repo.guardar.call_count == 2
    with pytest.raises(VentaNoModificable):
        caso.ejecutar(dto(1))
    assert len(agregado.pagos) == 2
    assert inventario.descontar.call_count == 2
    auditoria.registrar.assert_called_once()


def test_fallo_al_guardar_pago_parcial_no_toca_stock(entorno):
    _, repo, inventario, auditoria, uow = entorno
    fallo = RuntimeError("No se pudo guardar el pago parcial")
    repo.guardar.side_effect = fallo
    with pytest.raises(RuntimeError) as error:
        ProcesarPago(repo, inventario, auditoria, uow).ejecutar(dto(7))
    assert error.value is fallo
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()
    assert uow.__exit__.call_args.args[:2] == (RuntimeError, fallo)


def test_agregado_real_sin_productos_rechaza_el_pago(entorno):
    agregado, repo, inventario, auditoria, uow = entorno
    agregado.lineas.clear()
    with pytest.raises(VentaException, match="sin productos"):
        ProcesarPago(repo, inventario, auditoria, uow).ejecutar(dto())
    assert agregado.pagos == []
    repo.guardar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()
