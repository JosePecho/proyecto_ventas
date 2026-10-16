from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.reporting.application.use_cases.reporte_utilidad import ReporteUtilidad
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def utilidad_reporte_view(request):
    desde = request.GET.get("desde") or (date.today() - timedelta(days=30)).isoformat()
    hasta = request.GET.get("hasta") or date.today().isoformat()
    reporte = ReporteUtilidad(construir_reporte_repository()).ejecutar(
        date.fromisoformat(desde), date.fromisoformat(hasta)
    )
    return render(request, "dashboard/utilidad.html", {"reporte": reporte, "desde": desde, "hasta": hasta})

