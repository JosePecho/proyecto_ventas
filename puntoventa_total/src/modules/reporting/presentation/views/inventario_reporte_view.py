from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.reporting.application.use_cases.reporte_baja_rotacion import ReporteBajaRotacion
from src.modules.reporting.application.use_cases.reporte_stock_minimo import ReporteStockMinimo
from src.modules.reporting.application.use_cases.reporte_mayor_ganancia import ReporteMayorGanancia
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def inventario_reporte_view(request):
    repo = construir_reporte_repository()
    return render(
        request,
        "dashboard/inventario.html",
        {
            "stock_minimo": ReporteStockMinimo(repo).ejecutar(),
            "baja_rotacion": ReporteBajaRotacion(repo).ejecutar(),
            "mayor_ganancia": ReporteMayorGanancia(repo).por_margen(),
        },
    )

