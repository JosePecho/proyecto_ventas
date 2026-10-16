"""InnoDB real: dos escritores compiten por las mismas cinco unidades."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from django.db import close_old_connections, connection, connections, transaction

from src.modules.catalog.models import ProductoModel
from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
from src.modules.sales.infrastructure.adapters.inventario_adapter import InventarioAdapter

pytestmark = [
    pytest.mark.integration, pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(connection.vendor != "mysql", reason="Requiere InnoDB: ejecutar scripts/qa_inventory_mysql.py"),
]


@pytest.mark.parametrize("operacion", ["descontar", "reservar"])
def test_dos_escritores_no_pueden_consumir_el_mismo_stock(operacion):
    p = ProductoModel.objects.create(id=uuid4(), nombre="Concurrencia", codigo_barras="7751234567801",
                                    costo=Decimal("5"), precio_venta=Decimal("10"), estado="ACTIVO")
    ExistenciaModel.objects.create(id=uuid4(), producto_id=p.id, cantidad=5)
    LoteModel.objects.create(id=uuid4(), producto_id=p.id, numero_lote="L-CONC", cantidad_inicial=5,
                            cantidad_restante=5, fecha_recepcion=date.today())
    barrera = Barrier(2, timeout=10)

    def intentar():
        close_old_connections()
        try:
            barrera.wait()
            getattr(InventarioAdapter(), operacion)(str(p.id), 4, f"QA:{uuid4().hex[:8]}")
            return "aceptado"
        except StockInsuficiente:
            return "rechazado"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(intentar) for _ in range(2)]
        resultados = [f.result(timeout=25) for f in futuros]
    assert sorted(resultados) == ["aceptado", "rechazado"]
    existencia = ExistenciaModel.objects.get(producto_id=p.id)
    assert existencia.cantidad - existencia.reservada == 1
    assert 0 <= existencia.reservada <= existencia.cantidad
    if operacion == "descontar":
        assert existencia.cantidad == 1
        assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == 1
        assert MovimientoModel.objects.filter(producto_id=p.id, tipo="SALIDA_VENTA").count() == 1
    else:
        assert existencia.cantidad == 5 and existencia.reservada == 4


@pytest.mark.parametrize("operacion", ["liberar", "confirmar"])
def test_dos_operaciones_sobre_la_misma_reserva_no_afectan_otro_pedido(operacion):
    from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
    from src.modules.inventory.domain.exceptions.stock_exceptions import ReservaYaConfirmada
    from src.modules.inventory.infrastructure.factories import construir_reserva_repository, construir_stock_repository

    p = ProductoModel.objects.create(id=uuid4(), nombre="Reserva simultanea", codigo_barras="7751234567810",
                                    costo=5, precio_venta=10, estado="ACTIVO", stock_minimo=0)
    ExistenciaModel.objects.create(id=uuid4(), producto_id=p.id, cantidad=10)
    LoteModel.objects.create(id=uuid4(), producto_id=p.id, numero_lote="L-RES", cantidad_inicial=10,
                            cantidad_restante=10, fecha_recepcion=date.today())
    adapter = InventarioAdapter()
    primera = adapter.reservar(str(p.id), 3, "pedido-1")
    segunda = adapter.reservar(str(p.id), 2, "pedido-2")
    barrera = Barrier(2, timeout=10)

    def intentar():
        close_old_connections()
        try:
            barrera.wait()
            if operacion == "liberar":
                LiberarReserva(construir_stock_repository(), construir_reserva_repository(),
                               uow=transaction.atomic()).ejecutar(primera)
            else:
                InventarioAdapter().confirmar_reserva(primera, "pedido-1")
            return "aceptado"
        except ReservaYaConfirmada:
            return "rechazado"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(intentar) for _ in range(2)]
        resultados = sorted(f.result(timeout=25) for f in futuros)
    assert resultados == (["aceptado", "aceptado"] if operacion == "liberar" else ["aceptado", "rechazado"])
    existencia = ExistenciaModel.objects.get(producto_id=p.id)
    assert existencia.reservada == 2
    assert construir_reserva_repository().buscar_por_id(segunda).activa
    cantidad = 10 if operacion == "liberar" else 7
    assert existencia.cantidad == cantidad
    assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == cantidad
    assert MovimientoModel.objects.filter(producto_id=p.id, tipo="SALIDA_PEDIDO").count() == int(operacion == "confirmar")
    assert MovimientoModel.objects.filter(producto_id=p.id).count() == int(operacion == "confirmar")


def test_dos_primeras_recepciones_concurrentes_acumulan_stock():
    from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
    from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
    from src.modules.inventory.infrastructure.factories import (
        construir_lote_repository, construir_movimiento_repository, construir_stock_repository,
    )

    p = ProductoModel.objects.create(id=uuid4(), nombre="Primeras recepciones", codigo_barras="7751234567811",
                                    costo=5, precio_venta=10, estado="ACTIVO", stock_minimo=0)
    barrera = Barrier(2, timeout=10)

    def recibir(cantidad):
        close_old_connections()
        try:
            barrera.wait()
            RecibirMercaderia(construir_stock_repository(), construir_lote_repository(),
                construir_movimiento_repository(), uow=transaction.atomic()).ejecutar(
                    RecepcionLoteDTO(producto_id=str(p.id), numero_lote=f"L-{cantidad}",
                                     cantidad=cantidad, costo_unitario=Decimal("5")))
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(recibir, cantidad) for cantidad in (3, 4)]
        for futuro in futuros:
            futuro.result(timeout=25)
    assert ExistenciaModel.objects.filter(producto_id=p.id).count() == 1
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 7
    assert sum(LoteModel.objects.filter(producto_id=p.id).values_list("cantidad_restante", flat=True)) == 7
    assert MovimientoModel.objects.filter(producto_id=p.id).count() == 2
