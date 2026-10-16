from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from src.modules.reporting.application.use_cases.reporte_ventas_por_fecha import ReporteVentasPorFecha
from src.modules.reporting.infrastructure.factories import construir_exportador, construir_reporte_repository
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def ventas_reporte_view(request):
    desde = request.GET.get("desde") or (date.today() - timedelta(days=30)).isoformat()
    hasta = request.GET.get("hasta") or date.today().isoformat()
    formato = request.GET.get("formato")

    reporte = ReporteVentasPorFecha(construir_reporte_repository()).ejecutar(
        date.fromisoformat(desde), date.fromisoformat(hasta)
    )

    if formato in ("csv", "pdf"):
        contenido = construir_exportador(formato).exportar(
            encabezados=["Fecha", "Tickets", "Total", "IGV"],
            filas=[[f["fecha"], f["cantidad"], f["total"], f["igv"]] for f in reporte.por_dia],
            nombre="reporte_ventas",
        )
        respuesta = HttpResponse(contenido["contenido"], content_type=contenido["content_type"])
        respuesta["Content-Disposition"] = f'attachment; filename="{contenido["nombre_archivo"]}"'
        return respuesta

    return render(
        request,
        "dashboard/ventas.html",
        {"reporte": reporte, "desde": desde, "hasta": hasta},
    )

