"""Dashboard principal: metricas del dia y del mes."""
from __future__ import annotations


from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.reporting.application.use_cases.reporte_mayor_ganancia import ReporteMayorGanancia
from src.modules.reporting.application.use_cases.reporte_productos_mas_vendidos import ReporteProductosMasVendidos
from src.modules.reporting.application.use_cases.reporte_stock_minimo import ReporteStockMinimo
from src.modules.reporting.application.use_cases.reporte_ventas_diarias import ReporteVentasDiarias
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.identity.presentation.permissions.role_required import role_required
from django.utils import timezone


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def dashboard_view(request):
    repo = construir_reporte_repository()
    hoy = timezone.localdate()
    mes = RangoFechas.del_mes(hoy)
    return render(
        request,
        "dashboard/index.html",
        {
            "ventas_hoy": ReporteVentasDiarias(repo).ejecutar(hoy),
            "top_productos": ReporteProductosMasVendidos(repo).ejecutar(mes.desde, mes.hasta, 5),
            "mayor_ganancia": ReporteMayorGanancia(repo).ejecutar(mes.desde, mes.hasta, 5),
            "stock_minimo": ReporteStockMinimo(repo).ejecutar(),
        },
    )

