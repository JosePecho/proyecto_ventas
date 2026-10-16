from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.auditing.application.dto.auditoria_dto import FiltroAuditoriaDTO
from src.modules.auditing.application.use_cases.consultar_auditoria import ConsultarAuditoria
from src.modules.auditing.application.use_cases.rastrear_transaccion import RastrearTransaccion
from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.modules.auditing.infrastructure.factories import construir_auditoria_repository
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR")
def auditoria_view(request):
    repo = construir_auditoria_repository()
    filtros = FiltroAuditoriaDTO(
        accion=request.GET.get("accion") or None,
        entidad=request.GET.get("entidad") or None,
        entidad_id=request.GET.get("entidad_id") or None,
        desde=request.GET.get("desde") or None,
        hasta=request.GET.get("hasta") or None,
    )
    pagina = int(request.GET.get("pagina", 1) or 1)
    pagina_dto = ConsultarAuditoria(repo).ejecutar(filtros, pagina=pagina)

    traza = None
    if filtros.entidad and filtros.entidad_id:
        try:
            traza = RastrearTransaccion(repo).ejecutar(filtros.entidad, filtros.entidad_id)
        except Exception:
            traza = None

    return render(
        request,
        "auditing/registros.html",
        {"pagina_dto": pagina_dto, "filtros": filtros, "traza": traza},
    )

