from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel

from src.modules.customers.application.use_cases.calcular_frecuencia_compras import CalcularFrecuenciaCompras
from src.modules.customers.application.use_cases.consultar_historial_compras import ConsultarHistorialCompras
from src.modules.customers.infrastructure.factories import construir_cliente_repository, construir_historial_port


@login_required
def historial_compras_view(request, cliente_id):
    cliente = get_object_or_404(ClienteModel, pk=cliente_id)
    rol = request.session.get("rol")
    if rol not in ("ADMINISTRADOR", "GERENTE", "CAJERO") and not (
        rol == "CLIENTE" and str(cliente.usuario_id) == str(request.session.get("usuario_id"))
    ):
        return HttpResponseForbidden("No autorizado")
    repo, port = construir_cliente_repository(), construir_historial_port()
    historial = ConsultarHistorialCompras(repo, port).ejecutar(cliente_id)
    frecuencia = CalcularFrecuenciaCompras(repo, port).ejecutar(cliente_id)
    return render(
        request,
        "customers/historial.html",
        {"historial": historial, "frecuencia": frecuencia, "cliente_id": cliente_id},
    )

