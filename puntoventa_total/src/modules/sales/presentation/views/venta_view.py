"""Consulta de ventas del dia y detalle."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import render

from src.modules.sales.application.use_cases.consultar_venta import ConsultarVenta
from src.modules.sales.infrastructure.factories import construir_venta_repository
from src.modules.sales.presentation.permissions.venta_permissions import requiere_cajero


@login_required
@requiere_cajero
def ventas_dia_view(request):
    try:
        pagina = int(request.GET.get("pagina", 1) or 1)
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Pagina invalida")
    if pagina < 1:
        return HttpResponseBadRequest("Pagina invalida")
    pagina_dto = ConsultarVenta(construir_venta_repository()).del_dia(pagina=pagina)
    return render(request, "pos/carrito.html", {"pagina_dto": pagina_dto})

