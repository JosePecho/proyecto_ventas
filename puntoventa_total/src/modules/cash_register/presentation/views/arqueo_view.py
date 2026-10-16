from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.cash_register.application.use_cases.consultar_arqueo import ConsultarArqueo
from src.modules.cash_register.infrastructure.factories import construir_turno_repository, construir_ventas_turno_port
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
def arqueo_view(request):
    turno_id = request.GET.get("turno_id") or request.session.get("turno_caja_id")
    arqueo = None
    if turno_id:
        arqueo = ConsultarArqueo(construir_turno_repository(), construir_ventas_turno_port()).ejecutar(turno_id)
    return render(request, "cash_register/arqueo.html", {"arqueo": arqueo, "turno_id": turno_id})

