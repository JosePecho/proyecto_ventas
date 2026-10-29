from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from src.modules.sales.application.use_cases.emitir_ticket import EmitirTicket
from src.modules.sales.infrastructure.factories import construir_ticket_port, construir_venta_repository
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.presentation.permissions.venta_permissions import requiere_cajero


@login_required
@requiere_cajero
def ticket_view(request, venta_id):
    ventas = VentaModel.objects.all()
    if request.session.get("rol") == "CAJERO":
        ventas = ventas.filter(cajero_id=request.session.get("usuario_id"))
    get_object_or_404(ventas, pk=venta_id)
    ticket = EmitirTicket(construir_venta_repository(), construir_ticket_port()).ejecutar(venta_id)
    respuesta = HttpResponse(ticket["contenido"], content_type="application/pdf")
    respuesta["Content-Disposition"] = f'inline; filename="{ticket["nombre_archivo"]}"'
    return respuesta

