"""Contratos puros RF-044/045/047, sin ORM ni servicios."""
from datetime import date
from unittest.mock import Mock

import pytest

from src.modules.reporting.application.use_cases.reporte_utilidad import ReporteUtilidad
from src.modules.reporting.application.use_cases.reporte_ventas_diarias import ReporteVentasDiarias
from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.modules.reporting.domain.value_objects.utilidad_historica import agrupar_utilidad
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.modules.auditing.application.dto.auditoria_dto import FiltroAuditoriaDTO
from src.modules.auditing.application.use_cases.consultar_auditoria import ConsultarAuditoria
from src.modules.auditing.application.use_cases.registrar_auditoria import RegistrarAuditoria
from src.modules.auditing.application.use_cases.rastrear_transaccion import RastrearTransaccion
from src.modules.reporting.application.use_cases.reporte_ventas_por_fecha import ReporteVentasPorFecha
from src.modules.reporting.application.use_cases.reporte_productos_mas_vendidos import ReporteProductosMasVendidos
from src.shared.application.exceptions.application_exception import NotFoundException
from src.modules.identity.domain.entities.usuario import Usuario
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.catalog.domain.entities.categoria import Categoria

pytestmark = pytest.mark.unit


def fila(ingresos, costo, producto="pan"):
    return {"venta_id": producto, "producto_id": producto, "producto_nombre": producto,
            "cantidad": 1, "importe": ingresos, "total_venta": ingresos, "costo_unitario": costo}


@pytest.mark.parametrize("ingresos,costo,esperado", [
    (10, 6, 40.0), (10, 15, -50.0), (32, 31, 3.13),
    (0, 2, None), (10, None, None),
])
def test_margen_por_producto_es_utilidad_sobre_ingresos(ingresos, costo, esperado):
    resultado = agrupar_utilidad([fila(ingresos, costo)])[0]
    assert resultado["margen_pct"] == esperado


def test_margen_total_pondera_ingresos_en_lugar_de_promediar_porcentajes():
    repo = Mock(spec=ReporteRepository)
    repo.utilidad_por_producto.return_value = agrupar_utilidad([fila(10, 5), fila(90, 89, "torta")])
    reporte = ReporteUtilidad(repo).ejecutar(date(2026, 10, 1), date(2026, 10, 17))
    assert (reporte.ingresos_totales, reporte.costos_totales, reporte.utilidad_total) == (100, 94, 6)
    assert reporte.margen_pct == 6
    assert not reporte.estimado


def test_margen_total_y_producto_redondean_el_mismo_empate_decimal():
    repo = Mock(spec=ReporteRepository)
    repo.utilidad_por_producto.return_value = agrupar_utilidad([fila(32, 31)])
    reporte = ReporteUtilidad(repo).ejecutar(date(2026, 10, 17), date(2026, 10, 17))
    assert reporte.margen_pct == reporte.por_producto[0]["margen_pct"] == 3.13


def test_reporte_sin_ventas_es_cero_y_no_divide_por_cero():
    repo = Mock(spec=ReporteRepository)
    repo.utilidad_por_producto.return_value = []
    reporte = ReporteUtilidad(repo).ejecutar(date(2026, 10, 17), date(2026, 10, 17))
    assert reporte.ingresos_totales == reporte.costos_totales == reporte.utilidad_total == 0
    assert reporte.margen_pct == 0


@pytest.mark.parametrize("desde,hasta", [
    (date(2026, 10, 20), date(2026, 10, 19)), (date(2025, 1, 1), date(2026, 10, 17)),
])
def test_rango_invalido_no_consulta_repositorio(desde, hasta):
    repo = Mock(spec=ReporteRepository)
    with pytest.raises(ValidationException):
        ReporteUtilidad(repo).ejecutar(desde, hasta)
    repo.utilidad_por_producto.assert_not_called()


def test_reporte_diario_conserva_tickets_y_metodos_de_pago():
    repo = Mock(spec=ReporteRepository)
    dia = date(2026, 10, 17)
    repo.ventas_por_dia.return_value = [{"fecha": dia.isoformat(), "total": 40, "cantidad": 2}]
    repo.totales_por_metodo_pago.return_value = {"EFECTIVO": 10, "TARJETA": 30}
    reporte = ReporteVentasDiarias(repo).ejecutar(dia)
    assert (reporte["total"], reporte["tickets"], reporte["metodos_pago"]) == (
        40, 2, {"EFECTIVO": 10, "TARJETA": 30},
    )
    repo.ventas_por_dia.assert_called_once_with(dia, dia)


@pytest.mark.parametrize("accion", ["CREAR", "ACTUALIZAR", "ELIMINAR"])
def test_acciones_transversales_pueden_consultarse_como_dominio(accion):
    registro = RegistroAuditoria.crear(accion, "CategoriaModel", "categoria-1", "actor-1")
    assert (registro.accion, registro.usuario_id, registro.entidad_id) == (accion, "actor-1", "categoria-1")


def test_accion_arbitraria_sigue_rechazada():
    with pytest.raises(ValidationException):
        RegistroAuditoria.crear("ACCION_INVENTADA", "CategoriaModel", "categoria-1")


def test_ventas_por_rango_acumulan_tickets_total_e_igv():
    repo = Mock(spec=ReporteRepository)
    repo.ventas_por_dia.return_value = [
        {"fecha": "2026-10-16", "total": 10, "cantidad": 1, "igv": 1.8},
        {"fecha": "2026-10-17", "total": 30, "cantidad": 2, "igv": 5.4},
    ]
    reporte = ReporteVentasPorFecha(repo).ejecutar(date(2026, 10, 16), date(2026, 10, 17))
    assert (reporte.cantidad_tickets, reporte.total_ventas, reporte.total_igv) == (3, 40, 7.2)


def test_ranking_preserva_orden_y_limite_del_repositorio():
    repo = Mock(spec=ReporteRepository)
    repo.productos_mas_vendidos.return_value = [{"producto_id": "torta", "unidades": 5}]
    desde, hasta = date(2026, 10, 1), date(2026, 10, 17)
    assert ReporteProductosMasVendidos(repo).ejecutar(desde, hasta, 1) == [{"producto_id": "torta", "unidades": 5}]
    repo.productos_mas_vendidos.assert_called_once_with(desde, hasta, 1)


def test_auditoria_convierte_fechas_y_pagina_sin_alterar_el_actor():
    repo = Mock(spec=AuditoriaRepository)
    eventos = [RegistroAuditoria.crear("CREAR", "CategoriaModel", str(i), "actor") for i in range(3)]
    repo.consultar.return_value = eventos
    pagina = ConsultarAuditoria(repo).ejecutar(
        FiltroAuditoriaDTO(usuario_id="actor", desde="2026-10-01", hasta="2026-10-17"), pagina=2, por_pagina=2,
    )
    assert pagina.total == 3 and len(pagina.items) == 1
    assert pagina.items[0].entidad_id == "2" and pagina.items[0].usuario_id == "actor"
    assert repo.consultar.call_args.kwargs["desde"] == date(2026, 10, 1)
    assert repo.consultar.call_args.kwargs["hasta"] == date(2026, 10, 17)


def test_registrar_auditoria_conserva_actor_y_entidad():
    repo = Mock(spec=AuditoriaRepository)
    identificador = RegistrarAuditoria(repo).ejecutar("CREAR", "CategoriaModel", "cat-1", "actor")
    evento = repo.guardar.call_args.args[0]
    assert identificador == str(evento.id)
    assert (evento.usuario_id, evento.entidad_id) == ("actor", "cat-1")


def test_traza_conserva_primera_y_ultima_accion():
    repo = Mock(spec=AuditoriaRepository)
    repo.trazas_de_entidad.return_value = [
        RegistroAuditoria.crear("ACTUALIZAR", "CategoriaModel", "cat-1"),
        RegistroAuditoria.crear("CREAR", "CategoriaModel", "cat-1"),
    ]
    traza = RastrearTransaccion(repo).ejecutar("CategoriaModel", "cat-1")
    assert (traza["cantidad"], traza["primera_accion"], traza["ultima_accion"]) == (2, "CREAR", "ACTUALIZAR")


def test_traza_inexistente_se_informa():
    repo = Mock(spec=AuditoriaRepository)
    repo.trazas_de_entidad.return_value = []
    with pytest.raises(NotFoundException):
        RastrearTransaccion(repo).ejecutar("CategoriaModel", "inexistente")


@pytest.mark.parametrize("rol", list(RolUsuario))
def test_usuario_desactivado_no_puede_autenticarse_con_ningun_rol(rol):
    usuario = Usuario(username="usuario_qa", nombre_completo="Usuario QA", rol=rol)
    assert usuario.puede_autenticarse()
    usuario.desactivar()
    assert not usuario.puede_autenticarse()


def test_categoria_rechaza_nombre_vacio_al_editar_y_conserva_el_anterior():
    categoria = Categoria(nombre="Panes")
    with pytest.raises(ValidationException):
        categoria.renombrar("")
    assert categoria.nombre == "Panes"
