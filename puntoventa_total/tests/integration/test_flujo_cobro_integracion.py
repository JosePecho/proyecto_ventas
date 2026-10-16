"""Nivel 2 - Integracion: flujo de cobro real sobre repositorios Django + BD.

Prioriza infraestructura real (SQLite en config.settings.testing) sobre mocks
de BD: solo inventario/auditoria se aislan porque son puertos de otros
modulos (sus interacciones reales se prueban en tests/system).

Reglas verificadas: RN-06 (pago parcial no cierra; cierre con pago total),
RN-08 (vuelto >= 0) y la persistencia del agregado (venta + lineas + pagos).
"""
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.anular_venta import AnularVenta
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.infrastructure.factories import construir_venta_repository
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def _venta_guardada(numero_ticket: str, precio: str = "10.00") -> VentaAggregate:
    repo = construir_venta_repository()
    agregado = VentaAggregate(
        venta=Venta(
            numero_ticket=numero_ticket,
            cajero_id=str(uuid.uuid4()),
            turno_caja_id=str(uuid.uuid4()),
        )
    )
    agregado.agregar_producto(str(uuid.uuid4()), "Arroz 1kg", 1, Monto(Decimal(precio)))
    agregado.calcular_totales()
    repo.guardar(agregado)
    return agregado


def _pago(venta_id, monto: float, entregado: float | None = None) -> ProcesarPagoDTO:
    return ProcesarPagoDTO(
        venta_id=str(venta_id),
        metodo="EFECTIVO",
        monto=monto,
        monto_entregado=entregado,
    )


def test_pago_total_persiste_venta_pagada_su_pago_y_el_vuelto():
    repo = construir_venta_repository()
    inventario, auditoria = MagicMock(), MagicMock()
    venta = _venta_guardada("TINT-P1")

    resultado = ProcesarPago(repo, inventario, auditoria).ejecutar(
        _pago(venta.venta.id, monto=10.0, entregado=20.0)
    )

    assert resultado["estado"] == "PAGADA"
    assert resultado["vuelto"] == 10.0

    recuperada = repo.buscar_por_numero_ticket("TINT-P1")
    assert recuperada.venta.estado == EstadoVenta.PAGADA
    assert recuperada.venta.total == 10.0
    assert len(recuperada.pagos) == 1
    assert recuperada.pagos[0].vuelto.valor == Decimal("10.00")
    inventario.descontar.assert_called_once()
    assert inventario.descontar.call_args.args[2] == "VENTA:TINT-P1"  # referencia PEPS
    auditoria.registrar.assert_called_once()


def test_cobro_en_dos_pagos_parciales_cierra_recien_al_final():
    repo = construir_venta_repository()
    inventario, auditoria = MagicMock(), MagicMock()
    venta = _venta_guardada("TINT-P2")

    primero = ProcesarPago(repo, inventario, auditoria).ejecutar(_pago(venta.venta.id, monto=4.0))
    assert primero["estado"] == "PENDIENTE"
    assert primero["saldo"] == 6.0
    inventario.descontar.assert_not_called()  # RN-06: sin descuento hasta cobrar todo

    intermedia = repo.buscar_por_numero_ticket("TINT-P2")
    assert intermedia.venta.estado == EstadoVenta.BORRADOR
    assert len(intermedia.pagos) == 1

    segundo = ProcesarPago(repo, inventario, auditoria).ejecutar(
        _pago(venta.venta.id, monto=6.0, entregado=10.0)
    )
    assert segundo["estado"] == "PAGADA"
    assert segundo["vuelto"] == 4.0

    final = repo.buscar_por_numero_ticket("TINT-P2")
    assert final.venta.estado == EstadoVenta.PAGADA
    assert len(final.pagos) == 2
    assert sum((p.monto.valor for p in final.pagos), Decimal("0")) == Decimal("10.00")
    inventario.descontar.assert_called_once()


def test_pago_efectivo_entregado_insuficiente_es_rechazado_sin_persistir():
    repo = construir_venta_repository()
    inventario, auditoria = MagicMock(), MagicMock()
    venta = _venta_guardada("TINT-P3")
    from src.shared.domain.exceptions.validation_exception import ValidationException

    # RN-08: el efectivo entregado no puede ser menor al monto pagado
    with pytest.raises(ValidationException):
        ProcesarPago(repo, inventario, auditoria).ejecutar(_pago(venta.venta.id, monto=10.0, entregado=5.0))

    sin_cambios = repo.buscar_por_numero_ticket("TINT-P3")
    assert sin_cambios.venta.estado == EstadoVenta.BORRADOR
    assert len(sin_cambios.pagos) == 0
    inventario.descontar.assert_not_called()


def test_anulacion_persiste_estado_y_dispara_devolucion_de_stock():
    repo = construir_venta_repository()
    inventario, auditoria = MagicMock(), MagicMock()
    venta = _venta_guardada("TINT-P4")
    ProcesarPago(repo, inventario, auditoria).ejecutar(_pago(venta.venta.id, monto=10.0))
    inventario.descontar.reset_mock()
    inventario.devolver.reset_mock()
    auditoria.registrar.reset_mock()

    resultado = AnularVenta(repo, inventario, auditoria).ejecutar(
        str(venta.venta.id), "cliente se equivoco", str(uuid.uuid4())
    )

    assert resultado["estado"] == "ANULADA"
    anulada = repo.buscar_por_numero_ticket("TINT-P4")
    assert anulada.venta.estado == EstadoVenta.ANULADA
    assert anulada.venta.observacion == "cliente se equivoco"
    inventario.devolver.assert_called_once()  # solo si estaba pagada
    assert inventario.devolver.call_args.args[2] == "ANULACION:TINT-P4"
    auditoria.registrar.assert_called_once()
