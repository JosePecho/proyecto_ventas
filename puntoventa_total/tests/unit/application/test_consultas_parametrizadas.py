"""Consultas, alertas, DTOs y filtros con colecciones vacias y pobladas."""
from datetime import date, timedelta
from importlib import import_module
from unittest.mock import Mock

import pytest

from src.modules.auditing.application.dto.auditoria_dto import FiltroAuditoriaDTO
from src.modules.auditing.application.use_cases.consultar_auditoria import ConsultarAuditoria
from src.modules.auditing.application.use_cases.rastrear_transaccion import RastrearTransaccion
from src.modules.auditing.application.use_cases.registrar_auditoria import RegistrarAuditoria
from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.modules.inventory.application.use_cases.alertar_stock_minimo import AlertarStockMinimo
from src.modules.inventory.application.use_cases.alertar_vencimientos import AlertarVencimientos
from src.modules.inventory.application.use_cases.consultar_lotes import ConsultarLotes
from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.lote import Lote
from src.modules.reporting.application.use_cases.reporte_ventas_diarias import ReporteVentasDiarias
from src.modules.reporting.application.use_cases.reporte_ventas_por_fecha import ReporteVentasPorFecha
from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.shared.application.exceptions.application_exception import NotFoundException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("cantidad", [0, 1, 3])
def test_consulta_auditoria_conserva_total_y_detalle(cantidad):
    repo = Mock(spec=AuditoriaRepository)
    repo.consultar.return_value = [RegistroAuditoria.crear("CREAR", "Producto", str(i), detalle={"indice": i}) for i in range(cantidad)]
    pagina = ConsultarAuditoria(repo).ejecutar(FiltroAuditoriaDTO(), por_pagina=2)
    assert pagina.total == cantidad
    assert len(pagina.items) == min(cantidad, 2)
    assert [r.detalle["indice"] for r in pagina.items] == list(range(min(cantidad, 2)))


@pytest.mark.parametrize("accion", ["CREAR", "ACTUALIZAR", "ELIMINAR"])
def test_registrar_y_rastrear_auditoria(accion):
    repo = Mock(spec=AuditoriaRepository)
    identificador = RegistrarAuditoria(repo).ejecutar(accion, "Producto", "p1", detalle={"nombre": "Agua"})
    registro = repo.guardar.call_args.args[0]
    assert identificador == str(registro.id)
    repo.trazas_de_entidad.return_value = [registro]
    traza = RastrearTransaccion(repo).ejecutar("Producto", "p1")
    assert traza["cantidad"] == 1
    assert traza["primera_accion"] == traza["ultima_accion"] == accion
    assert traza["eventos"][0].detalle == {"nombre": "Agua"}


@pytest.mark.parametrize("entidad", ["Producto", "Venta"])
def test_rastro_ausente_es_error(entidad):
    repo = Mock(spec=AuditoriaRepository)
    repo.trazas_de_entidad.return_value = []
    with pytest.raises(NotFoundException):
        RastrearTransaccion(repo).ejecutar(entidad, "inexistente")


@pytest.mark.parametrize("cantidad", [0, 1, 3])
def test_alertas_stock_y_vencimiento_notifican_cada_elemento(cantidad):
    repo, notificador = Mock(), Mock()
    repo.productos_bajo_minimo.return_value = [{"producto_id": f"p{i}", "disponible": 0, "stock_minimo": 2} for i in range(cantidad)]
    assert AlertarStockMinimo(repo, notificador).ejecutar() == cantidad
    assert notificador.notificar_stock_minimo.call_count == cantidad
    repo.lotes_por_vencer.return_value = [Lote(producto_id=f"p{i}", numero_lote=f"L{i}", cantidad_inicial=1,
                                              fecha_vencimiento=date.today() + timedelta(days=3)) for i in range(cantidad)]
    assert AlertarVencimientos(repo, notificador).ejecutar() == cantidad
    assert notificador.notificar_vencimiento.call_count == cantidad


@pytest.mark.parametrize("cantidad,reservada,umbral,bajo", [(0, 0, 5, True), (5, 0, 5, False), (5, 1, 5, True), (10, 2, 0, False)])
def test_consulta_stock_respeta_reserva_y_umbral(cantidad, reservada, umbral, bajo):
    repo = Mock()
    repo.obtener.return_value = Existencia(producto_id="p1", cantidad=cantidad, reservada=reservada)
    repo.umbral_minimo.return_value = umbral
    dto = ConsultarStock(repo).ejecutar("p1")
    assert dto.disponible == cantidad - reservada
    assert dto.bajo_minimo is bajo


@pytest.mark.parametrize("cantidad", [0, 1, 3])
def test_consultar_lotes_convierte_y_conserva_filas(cantidad):
    repo = Mock()
    repo.listar_por_producto.return_value = [Lote(producto_id="p1", numero_lote=f"L{i}", cantidad_inicial=2,
                                                  cantidad_restante=1, costo_unitario=Monto("5.01")) for i in range(cantidad)]
    dtos = ConsultarLotes(repo).ejecutar("p1")
    assert len(dtos) == cantidad
    assert [d.numero_lote for d in dtos] == [f"L{i}" for i in range(cantidad)]
    assert all(d.costo_unitario == 5.01 for d in dtos)


@pytest.mark.parametrize("cantidad", [0, 1, 3])
def test_reportes_ventas_conservan_totales_e_impuestos(cantidad):
    repo = Mock(spec=ReporteRepository)
    repo.ventas_por_dia.return_value = [{"total": 100, "igv": 18, "cantidad": 2} for _ in range(cantidad)]
    repo.totales_por_metodo_pago.return_value = {"EFECTIVO": 100 * cantidad}
    dia = date(2026, 10, 30)
    diario = ReporteVentasDiarias(repo).ejecutar(dia)
    rango = ReporteVentasPorFecha(repo).ejecutar(dia, dia)
    assert diario["total"] == rango.total_ventas == 100 * cantidad
    assert diario["tickets"] == rango.cantidad_tickets == 2 * cantidad
    assert rango.total_igv == 18 * cantidad


@pytest.mark.parametrize("limite", [1, 2, 10])
def test_ranking_transmite_limite(limite):
    from src.modules.reporting.application.use_cases.reporte_productos_mas_vendidos import (
        ReporteProductosMasVendidos,
    )

    repo = Mock(spec=ReporteRepository)
    repo.productos_mas_vendidos.return_value = [{"producto_id": "p1", "cantidad": 10}]
    dia = date(2026, 10, 30)
    assert ReporteProductosMasVendidos(repo).ejecutar(dia, dia, limite) == [{"producto_id": "p1", "cantidad": 10}]
    repo.productos_mas_vendidos.assert_called_once_with(dia, dia, limite)


@pytest.mark.parametrize("modulo,entidad,archivo,clase,datos", [
    ("catalog", "categoria.Categoria", "categoria_dto", "CategoriaDTO", {"nombre": "Agua"}),
    ("customers", "cliente.Cliente", "cliente_output", "ClienteOutputDTO", {"nombre": "Ana"}),
    ("identity", "usuario.Usuario", "usuario_output", "UsuarioOutputDTO", {"username": "ana1", "nombre_completo": "Ana"}),
    ("promotions", "promocion.Promocion", "promocion_output", "PromocionOutputDTO", {"nombre": "Oferta"}),
])
@pytest.mark.parametrize("activo", [False, True])
def test_dtos_salida_conservan_identidad_y_estado(modulo, entidad, archivo, clase, datos, activo):
    fichero, nombre = entidad.split(".")
    tipo = getattr(import_module(f"src.modules.{modulo}.domain.entities.{fichero}"), nombre)
    origen = tipo(**datos, activo=activo)
    dto_cls = getattr(import_module(f"src.modules.{modulo}.application.dto.{archivo}"), clase)
    dto = dto_cls.desde_entidad(origen)
    assert dto.id == str(origen.id)
    if hasattr(dto, "activo"):
        assert dto.activo is activo
    if hasattr(dto, "estado"):
        assert dto.estado == origen.estado.value


@pytest.mark.parametrize("categoria", ["categoria-1", "categoria-2"])
@pytest.mark.parametrize("pagina", [1, 2])
def test_filtro_categoria_conserva_filtro_y_paginacion(categoria, pagina):
    from src.modules.catalog.application.use_cases.filtrar_por_categoria import FiltrarPorCategoria
    from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository

    repo = Mock(spec=ProductoRepository)
    repo.contar.return_value = 30
    repo.listar.return_value = []
    resultado = FiltrarPorCategoria(repo).ejecutar(categoria, pagina, 10)
    assert resultado.pagina == pagina
    assert resultado.total == 30
    assert repo.listar.call_args.kwargs["categoria_id"] == categoria
    assert repo.listar.call_args.kwargs["offset"] == (pagina - 1) * 10


@pytest.mark.parametrize("umbral", [0, 5, 10])
def test_contrato_stock_umbral_predeterminado(umbral):
    from src.modules.inventory.domain.repositories.stock_repository import StockRepository

    assert StockRepository.umbral_minimo(Mock(), "p1", umbral) == umbral


@pytest.mark.parametrize("cantidad", [0, 1, 3])
def test_contrato_movimiento_cuenta_kardex_completo(cantidad):
    from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository

    repo = Mock()
    repo.kardex.return_value = [object() for _ in range(cantidad)]
    assert MovimientoRepository.contar_kardex(repo, "p1") == cantidad
    repo.kardex.assert_called_once_with("p1", None, None, limite=None)


@pytest.mark.parametrize("cantidad", [1, 3])
@pytest.mark.parametrize("tipo", ["pedido", "venta"])
def test_dto_agregado_conserva_lineas_y_total(tipo, cantidad):
    from src.modules.orders.application.dto.pedido_output import PedidoOutputDTO
    from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
    from src.modules.orders.domain.entities.pedido import Pedido
    from src.modules.sales.application.dto.venta_output import VentaOutputDTO
    from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
    from src.modules.sales.domain.entities.venta import Venta

    agregado = PedidoAggregate(Pedido(cliente_nombre="Ana")) if tipo == "pedido" else VentaAggregate(Venta())
    agregado.agregar_producto("p1", "Agua", cantidad, Monto("9.99"))
    if tipo == "venta":
        agregado.calcular_totales()
    dto = (PedidoOutputDTO if tipo == "pedido" else VentaOutputDTO).desde_agregado(agregado)
    assert dto.estado == "BORRADOR"
    assert dto.total == float(Monto("9.99").valor * cantidad)
    assert len(dto.lineas) == 1
    if tipo == "pedido":
        assert dto.estado_label == "Carrito"
