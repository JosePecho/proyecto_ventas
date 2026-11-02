"""Caja blanca del coordinador de cobro; puertos y agregado aislados con mocks."""
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.ports.auditoria_port import AuditoriaPort
from src.modules.sales.application.ports.inventario_port import InventarioPort
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


@pytest.fixture
def cobro():
    agregado = Mock(spec=VentaAggregate)
    agregado.venta = Venta(cajero_id="cajero-11", numero_ticket="S11-001")
    agregado.venta.total = 10.0
    agregado.lineas = []
    agregado.saldo_pendiente.return_value = Decimal("0")
    agregado.cerrar.side_effect = lambda: setattr(agregado.venta, "estado", EstadoVenta.PAGADA)
    repo, inventario, auditoria = Mock(spec=VentaRepository), Mock(spec=InventarioPort), Mock(spec=AuditoriaPort)
    repo.buscar_por_id.return_value = agregado
    return agregado, repo, inventario, auditoria


def datos(metodo="EFECTIVO", entregado=None, monto=10.0):
    return ProcesarPagoDTO("venta-11", metodo, monto, entregado, "operacion-11")


def linea(requiere_stock=True, cantidad=1):
    detalle = DetalleVenta(producto_id="producto-11", producto_nombre="Arroz", precio_unitario=Monto(10))
    detalle.requiere_stock = requiere_stock
    # Estado sintetico para comprobar la guarda defensiva; el constructor rechaza cero.
    detalle.cantidad = cantidad
    return detalle


def test_b01_venta_inexistente(cobro):
    agregado, repo, inventario, auditoria = cobro
    repo.buscar_por_id.return_value = None
    with pytest.raises(VentaNoEncontrada):
        ProcesarPago(repo, inventario, auditoria).ejecutar(datos())
    agregado.registrar_pago.assert_not_called()
    repo.guardar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()


@pytest.mark.parametrize("promociones,metodo,entregado,vuelto", [
    (False, "EFECTIVO", None, None),  # B02
    (True, "EFECTIVO", None, None),   # B03
    (False, "EFECTIVO", 12.0, Decimal("2.00")),  # B04
    (False, "TARJETA", 12.0, None),  # B05: segundo operando del and falso
], ids=["B02", "B03", "B04", "B05"])
def test_pago_parcial(cobro, promociones, metodo, entregado, vuelto):
    agregado, repo, inventario, auditoria = cobro
    agregado.saldo_pendiente.return_value = Decimal("4.25")
    puerto_promociones = Mock() if promociones else None
    with patch("src.modules.sales.application.use_cases.preparar_beneficios.PrepararBeneficiosVenta") as preparar:
        resultado = ProcesarPago(repo, inventario, auditoria, promociones=puerto_promociones).ejecutar(
            datos(metodo, entregado)
        )
    assert resultado == {"estado": "PENDIENTE", "saldo": 4.25}
    pago = agregado.registrar_pago.call_args.args[0]
    assert (pago.vuelto.valor if pago.vuelto is not None else None) == vuelto
    assert pago.metodo.tipo == metodo
    assert pago.monto == Monto(10)
    if promociones:
        preparar.assert_called_once_with(repo, puerto_promociones)
        preparar.return_value.aplicar.assert_called_once_with(agregado)
    else:
        preparar.assert_not_called()
    repo.guardar.assert_called_once_with(agregado)
    agregado.cerrar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()


@pytest.mark.parametrize("lineas,entregado,descuentos,vuelto", [
    ([], None, 0, 0.0),  # B06: agregado sintetico vacio, salida inmediata del bucle
    ([linea()], None, 1, 0.0),  # B07
    ([linea(False)], None, 0, 0.0),  # B08
    ([linea(cantidad=0)], None, 0, 0.0),  # B09: guarda defensiva
    ([], 12.0, 0, 2.0),  # B10
    ([linea(), linea(False), linea(cantidad=0)], 10.0, 1, 0.0),  # R01
], ids=["B06", "B07", "B08", "B09", "B10", "R01"])
def test_pago_completo(cobro, lineas, entregado, descuentos, vuelto):
    agregado, repo, inventario, auditoria = cobro
    agregado.lineas = lineas
    resultado = ProcesarPago(repo, inventario, auditoria).ejecutar(datos(entregado=entregado))
    assert resultado == {"estado": "PAGADA", "total": 10.0, "vuelto": vuelto, "numero_ticket": "S11-001"}
    assert inventario.descontar.call_count == descuentos
    if descuentos:
        inventario.descontar.assert_called_once_with("producto-11", 1, "VENTA:S11-001", "cajero-11")
    agregado.cerrar.assert_called_once_with()
    repo.guardar.assert_called_once_with(agregado)
    auditoria.registrar.assert_called_once_with(
        accion="VENTA_PAGADA", entidad="Venta", entidad_id=str(agregado.venta.id), usuario_id="cajero-11",
        detalle={"total": 10.0, "metodo": "EFECTIVO", "numero_ticket": "S11-001"},
    )


@pytest.mark.parametrize("monto,entregado,esperado", [
    (0.1, 0.3, "0.20"), (8.5, 10.0, "1.50"), (10.0, 10.0, "0.00"),
])
def test_regresion_redondeo_vuelto(cobro, monto, entregado, esperado):
    agregado, repo, inventario, auditoria = cobro
    resultado = ProcesarPago(repo, inventario, auditoria).ejecutar(datos(entregado=entregado, monto=monto))
    assert agregado.registrar_pago.call_args.args[0].vuelto.valor == Decimal(esperado)
    assert resultado["vuelto"] == float(esperado)


def test_efectivo_insuficiente_no_guarda(cobro):
    agregado, repo, inventario, auditoria = cobro
    with pytest.raises(ValidationException):
        ProcesarPago(repo, inventario, auditoria).ejecutar(datos(entregado=9.0))
    agregado.registrar_pago.assert_not_called()
    repo.guardar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()


def vuelto_propuesto_ia(pago_datos, moneda):
    """Propuesta deliberadamente incorrecta; nunca se incorpora a produccion."""
    return (
        Monto(pago_datos.monto_entregado - pago_datos.monto, moneda)
        if pago_datos.monto_entregado and pago_datos.metodo == "EFECTIVO" else None
    )


def test_auditoria_rechaza_simplificacion_por_truthiness(cobro):
    _, repo, inventario, auditoria = cobro
    pago_datos = datos(entregado=0.0)
    assert vuelto_propuesto_ia(pago_datos, "PEN") is None
    with pytest.raises(ValidationException):
        ProcesarPago(repo, inventario, auditoria).ejecutar(pago_datos)
    repo.guardar.assert_not_called()


def test_auditoria_rechaza_redondeo_binario():
    assert Monto(Decimal("1.005")).valor == Decimal("1.01")
    assert Decimal(str(round(1.005, 2))) == Decimal("1.00")
