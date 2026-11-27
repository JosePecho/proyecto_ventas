"""Rollback durable del cobro con repositorios y adaptadores reales."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import connection, transaction

from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.catalog.models import ProductoModel
from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel
from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoModificable
from src.modules.sales.infrastructure.adapters.inventario_adapter import InventarioAdapter
from src.modules.sales.infrastructure.auditing.auditoria_adapter import AuditoriaAdapter
from src.modules.sales.infrastructure.persistence.django_models.detalle_venta_model import DetalleVentaModel
from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.infrastructure.persistence.repositories.django_venta_repository import (
    DjangoVentaRepository,
)
from src.shared.domain.value_objects.monto import Monto
from src.shared.infrastructure.database.mysql_unit_of_work import MySQLUnitOfWork

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True)]


@pytest.fixture
def venta_persistida():
    agregado = VentaAggregate(Venta(numero_ticket=f"S11-{uuid4().hex[:12]}", cajero_id=str(uuid4())))
    for indice in range(2):
        producto = ProductoModel.objects.create(
            id=uuid4(), nombre=f"Producto S11 {indice}", codigo_barras=f"775{uuid4().int % 10**10:010d}",
            costo=Decimal("5"), precio_venta=Decimal("10"), estado="ACTIVO", requiere_stock=True,
        )
        ExistenciaModel.objects.create(id=uuid4(), producto_id=producto.id, cantidad=20, reservada=0)
        LoteModel.objects.create(
            id=uuid4(), producto_id=producto.id, numero_lote=f"S11-{indice}", cantidad_inicial=20,
            cantidad_restante=20, fecha_recepcion=date.today(),
        )
        agregado.agregar_producto(str(producto.id), producto.nombre, 1, Monto(10))
    agregado.calcular_totales()
    DjangoVentaRepository().guardar(agregado)
    assert not connection.in_atomic_block  # la semilla ya esta confirmada
    return str(agregado.venta.id)


def snapshot():
    modelos = (VentaModel, DetalleVentaModel, PagoModel, ExistenciaModel, LoteModel, MovimientoModel, AuditoriaModel)
    return {modelo._meta.label: list(modelo.objects.order_by("pk").values()) for modelo in modelos}


@pytest.mark.parametrize("tipo_uow", ["atomic", "mysql_uow"])
@pytest.mark.parametrize("etapa", ["inventario", "guardar", "auditar"])
def test_fallo_restaura_toda_la_bd_y_permite_reintentar(venta_persistida, tipo_uow, etapa):
    antes = snapshot()
    repo, inventario, auditoria = DjangoVentaRepository(), InventarioAdapter(), AuditoriaAdapter()
    uow = transaction.atomic() if tipo_uow == "atomic" else MySQLUnitOfWork()
    llamadas = []
    objeto, metodo = {
        "inventario": (inventario, "descontar"), "guardar": (repo, "guardar"), "auditar": (auditoria, "registrar"),
    }[etapa]
    original = getattr(objeto, metodo)
    fallo = RuntimeError(f"Fallo despues de escribir: {etapa}")

    def escribir_y_fallar(*args, **kwargs):
        resultado = original(*args, **kwargs)
        llamadas.append(1)
        # Fallar tras escribir el segundo producto prueba el rollback del bucle completo.
        if etapa != "inventario" or len(llamadas) == 2:
            assert snapshot() != antes
            raise fallo
        return resultado

    datos = ProcesarPagoDTO(venta_persistida, "EFECTIVO", 20, 20)
    with patch.object(objeto, metodo, side_effect=escribir_y_fallar), pytest.raises(RuntimeError) as error:
        ProcesarPago(repo, inventario, auditoria, uow).ejecutar(datos)
    assert error.value is fallo
    assert len(llamadas) == (2 if etapa == "inventario" else 1)
    assert not connection.in_atomic_block
    assert snapshot() == antes  # incluye pagos, estado, lotes, existencias, kardex y auditoria

    # Releer desde otra instancia evita validar solo el estado en memoria del intento fallido.
    resultado = ProcesarPago(
        DjangoVentaRepository(), InventarioAdapter(), AuditoriaAdapter(), transaction.atomic()
    ).ejecutar(datos)
    assert resultado["estado"] == "PAGADA"
    assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 1
    assert list(ExistenciaModel.objects.values_list("cantidad", flat=True)) == [19, 19]
    assert MovimientoModel.objects.filter(tipo="SALIDA_VENTA").count() == 2
    assert AuditoriaModel.objects.filter(accion="VENTA_PAGADA").count() == 1


def test_dos_pagos_persistidos_sin_doble_descuento(venta_persistida):
    def cobrar(monto):
        return ProcesarPago(
            DjangoVentaRepository(), InventarioAdapter(), AuditoriaAdapter(), transaction.atomic()
        ).ejecutar(ProcesarPagoDTO(venta_persistida, "EFECTIVO", monto, monto))

    assert cobrar(7) == {"estado": "PENDIENTE", "saldo": 13.0}
    assert VentaModel.objects.get(pk=venta_persistida).estado == "BORRADOR"
    assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 1
    assert list(ExistenciaModel.objects.values_list("cantidad", flat=True)) == [20, 20]
    assert not MovimientoModel.objects.exists()
    assert not AuditoriaModel.objects.exists()
    assert cobrar(13)["estado"] == "PAGADA"
    assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 2
    assert list(ExistenciaModel.objects.values_list("cantidad", flat=True)) == [19, 19]
    assert MovimientoModel.objects.count() == 2
    assert AuditoriaModel.objects.filter(accion="VENTA_PAGADA").count() == 1
    antes_repeticion = snapshot()
    with pytest.raises(VentaNoModificable):
        cobrar(1)
    assert snapshot() == antes_repeticion


@pytest.mark.parametrize("tipo_uow", ["atomic", "mysql_uow"])
def test_rollback_de_pago_parcial_y_reintento(venta_persistida, tipo_uow):
    antes = snapshot()
    repo = DjangoVentaRepository()
    guardar_original = repo.guardar

    def guardar_y_fallar(agregado):
        guardar_original(agregado)
        assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 1
        raise RuntimeError("Fallo despues de persistir pago parcial")

    uow = transaction.atomic() if tipo_uow == "atomic" else MySQLUnitOfWork()
    with patch.object(repo, "guardar", side_effect=guardar_y_fallar), pytest.raises(RuntimeError, match="pago parcial"):
        ProcesarPago(repo, InventarioAdapter(), AuditoriaAdapter(), uow).ejecutar(
            ProcesarPagoDTO(venta_persistida, "EFECTIVO", 7, 7)
        )
    assert not connection.in_atomic_block
    assert snapshot() == antes
    resultado = ProcesarPago(
        DjangoVentaRepository(), InventarioAdapter(), AuditoriaAdapter(), transaction.atomic()
    ).ejecutar(ProcesarPagoDTO(venta_persistida, "EFECTIVO", 7, 7))
    assert resultado == {"estado": "PENDIENTE", "saldo": 13.0}
    assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 1
    assert list(ExistenciaModel.objects.values_list("cantidad", flat=True)) == [20, 20]
    assert not MovimientoModel.objects.exists()
    assert not AuditoriaModel.objects.exists()
