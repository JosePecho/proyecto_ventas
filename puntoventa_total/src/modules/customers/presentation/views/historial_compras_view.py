from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.customers.application.use_cases.calcular_frecuencia_compras import CalcularFrecuenciaCompras
from src.modules.customers.application.use_cases.consultar_historial_compras import ConsultarHistorialCompras
from src.modules.customers.infrastructure.factories import construir_cliente_repository, construir_historial_port
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
def historial_compras_view(request, cliente_id):
    repo, port = construir_cliente_repository(), construir_historial_port()
    historial = ConsultarHistorialCompras(repo, port).ejecutar(cliente_id)
    frecuencia = CalcularFrecuenciaCompras(repo, port).ejecutar(cliente_id)
    return render(
        request,
        "customers/historial.html",
        {"historial": historial, "frecuencia": frecuencia, "cliente_id": cliente_id},
    )

