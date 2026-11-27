"""Colaboracion real entre modulos sobre la BD aislada de pruebas."""
from datetime import date
from uuid import uuid4

import pytest
from django.db import transaction

from src.modules.cash_register.infrastructure.adapters.ventas_turno_adapter import VentasTurnoAdapter
from src.modules.catalog.infrastructure.adapters.disponibilidad_adapter import DisponibilidadAdapter
from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.customers.infrastructure.adapters.historial_compras_adapter import HistorialComprasAdapter
from src.modules.inventory.infrastructure.factories import construir_stock_repository
from src.modules.orders.infrastructure.adapters.inventario_adapter import (
    InventarioAdapter as InventarioPedidos,
)
from src.modules.promotions.infrastructure.adapters.frecuencia_cliente_adapter import FrecuenciaClienteAdapter
from src.modules.reporting.infrastructure.persistence.repositories.django_reporte_repository import (
    DjangoReporteRepository,
)
from src.modules.sales.application.dto.venta_input import CrearVentaDTO, ProcesarPagoDTO
from src.modules.sales.application.use_cases.agregar_producto import AgregarProducto
from src.modules.sales.application.use_cases.anular_venta import AnularVenta
from src.modules.sales.application.use_cases.crear_venta import CrearVenta
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.infrastructure.factories import (
    construir_auditoria_port,
    construir_inventario_port,
    construir_promociones_port,
    construir_venta_repository,
)
from tests.factories.catalogo_web import producto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.mark.parametrize("cantidad", [1, 2])
@pytest.mark.parametrize("metodo", ["EFECTIVO", "YAPE"])
def test_cobro_reportes_y_anulacion_con_adaptadores_reales(cantidad, metodo):
    p = producto(cantidad=10)
    repo = construir_venta_repository()
    inventario, promociones, auditoria = construir_inventario_port(), construir_promociones_port(), construir_auditoria_port()
    cajero, turno, cliente = str(uuid4()), str(uuid4()), str(uuid4())
    dto = CrearVenta(repo).ejecutar(CrearVentaDTO(cajero, turno, cliente))
    entidad_producto = construir_producto_repository().buscar_por_id(p.id)
    agregado = AgregarProducto(repo, inventario, promociones).ejecutar(dto.id, entidad_producto, cantidad)
    assert agregado.total == 10 * cantidad
    resultado = ProcesarPago(repo, inventario, auditoria, uow=transaction.atomic()).ejecutar(
        ProcesarPagoDTO(dto.id, metodo, 10 * cantidad, referencia="ref-param")
    )
    assert resultado["estado"] == "PAGADA"
    assert construir_stock_repository().disponible(str(p.id)) == 10 - cantidad
    disponibilidad = DisponibilidadAdapter()
    assert disponibilidad.stock_disponible(str(p.id)) == 10 - cantidad
    assert disponibilidad.stock_disponible_lote([str(p.id)]) == {str(p.id): 10 - cantidad}
    assert not disponibilidad.tiene_stock_minimo(str(p.id))
    ventas = VentasTurnoAdapter()
    assert ventas.total_ventas(turno) == 10 * cantidad
    assert ventas.contar_ventas(turno) == 1
    assert len(ventas.pagos_del_turno(turno)) == 1
    historial = HistorialComprasAdapter()
    assert historial.total_gastado(cliente) == 10 * cantidad
    assert len(historial.compras_del_cliente(cliente)) == 1
    assert FrecuenciaClienteAdapter().compras_previas(cliente) == 1
    assert FrecuenciaClienteAdapter().clasificacion(cliente) == "SIN_DATOS"
    reporte = DjangoReporteRepository()
    dia = date.today()
    assert sum(f["cantidad"] for f in reporte.ventas_por_dia(dia, dia)) == 1
    assert reporte.totales_por_metodo_pago(dia, dia)[metodo] == 10 * cantidad
    assert reporte.productos_mas_vendidos(dia, dia)[0]["unidades"] == cantidad
    AnularVenta(repo, inventario, auditoria, uow=transaction.atomic()).ejecutar(dto.id, "Prueba", cajero)
    assert construir_stock_repository().disponible(str(p.id)) == 10
    assert historial.total_gastado(cliente) == 0


@pytest.mark.parametrize("cantidad", [1, 3])
@pytest.mark.parametrize("confirmar", [False, True])
def test_reserva_pedidos_libera_o_confirma_stock(cantidad, confirmar):
    p = producto(cantidad=10)
    adaptador = InventarioPedidos()
    reserva_id = adaptador.reservar(str(p.id), cantidad, "PEDIDO:PARAM")
    assert adaptador.stock_disponible(str(p.id)) == 10 - cantidad
    if confirmar:
        assert adaptador.confirmar_reserva(reserva_id, "PEDIDO:PARAM") == 10 - cantidad
    else:
        adaptador.liberar(reserva_id)
        assert adaptador.stock_disponible(str(p.id)) == 10


@pytest.mark.parametrize("metodo", ["GET", "POST", "PATCH", "DELETE"])
@pytest.mark.parametrize("estado", [200, 400])
def test_middleware_auditoria_limpia_contexto_y_revierte_error(metodo, estado, rf):
    from django.contrib.auth.models import AnonymousUser
    from django.http import HttpResponse

    from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
    from src.modules.auditing.infrastructure.request_audit import RequestAuditMiddleware, contexto
    from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel

    request = getattr(rf, metodo.lower())("/prueba-parametrizada/")
    request.session = {}
    request.user = AnonymousUser()
    slug = "middleware-parametrizado"

    def responder(request):
        CategoriaModel.objects.create(id=uuid4(), nombre="Prueba", slug=slug)
        return HttpResponse(status=estado)

    respuesta = RequestAuditMiddleware(responder)(request)
    assert respuesta.status_code == estado
    assert contexto.get() is None
    mutacion = metodo != "GET"
    assert CategoriaModel.objects.filter(slug=slug).exists() is (not mutacion or estado < 400)
    registros = AuditoriaModel.objects.filter(detalle__ruta="/prueba-parametrizada/")
    assert registros.count() == (1 if mutacion and estado < 400 else 0)
