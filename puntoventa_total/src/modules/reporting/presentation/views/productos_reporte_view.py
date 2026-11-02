from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.identity.presentation.permissions.role_required import role_required
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.reporting.presentation.forms.rango_reporte_form import RangoReporteForm


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def productos_reporte_view(request):
    form = RangoReporteForm.de_request(request)
    if not form.is_valid():
        return render(request, "dashboard/productos.html", {"form": form}, status=400)
    desde, hasta = form.cleaned_data["desde"], form.cleaned_data["hasta"]
    filas = construir_reporte_repository().productos_mas_vendidos(desde, hasta, None, orden=request.GET.get("orden", "monto"))
    return render(request, "dashboard/productos.html", {"productos": filas})
