from __future__ import annotations


from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.reporting.application.use_cases.reporte_utilidad import ReporteUtilidad
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.identity.presentation.permissions.role_required import role_required
from src.modules.reporting.presentation.forms.rango_reporte_form import RangoReporteForm


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def utilidad_reporte_view(request):
    form = RangoReporteForm.de_request(request)
    if not form.is_valid():
        return render(request, "dashboard/utilidad.html", {"form": form}, status=400)
    desde, hasta = form.cleaned_data["desde"], form.cleaned_data["hasta"]
    reporte = ReporteUtilidad(construir_reporte_repository()).ejecutar(
        desde, hasta
    )
    return render(request, "dashboard/utilidad.html", {"reporte": reporte, "desde": desde, "hasta": hasta})

