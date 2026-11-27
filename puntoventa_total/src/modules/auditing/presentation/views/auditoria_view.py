from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.auditing.application.dto.auditoria_dto import FiltroAuditoriaDTO
from src.modules.auditing.application.use_cases.consultar_auditoria import ConsultarAuditoria
from src.modules.auditing.application.use_cases.rastrear_transaccion import RastrearTransaccion
from src.modules.auditing.infrastructure.factories import construir_auditoria_repository
from src.modules.auditing.presentation.forms.filtro_auditoria_form import FiltroAuditoriaForm
from src.modules.identity.presentation.permissions.role_required import role_required
from src.shared.application.exceptions.application_exception import NotFoundException


@login_required
@role_required("ADMINISTRADOR")
def auditoria_view(request):
    form = FiltroAuditoriaForm(request.GET)
    if not form.is_valid():
        return render(request, "auditing/registros.html", {"form": form, "filtros": request.GET}, status=400)
    datos = form.cleaned_data
    repo = construir_auditoria_repository()
    filtros = FiltroAuditoriaDTO(
        accion=datos.get("accion") or None,
        entidad=datos.get("entidad") or None,
        entidad_id=datos.get("entidad_id") or None,
        usuario_id=str(datos["usuario_id"]) if datos.get("usuario_id") else None,
        desde=datos["desde"].isoformat() if datos.get("desde") else None,
        hasta=datos["hasta"].isoformat() if datos.get("hasta") else None,
    )
    pagina = datos.get("pagina") or 1
    pagina_dto = ConsultarAuditoria(repo).ejecutar(filtros, pagina=pagina)

    traza = None
    if filtros.entidad and filtros.entidad_id:
        try:
            traza = RastrearTransaccion(repo).ejecutar(filtros.entidad, filtros.entidad_id)
        except NotFoundException:
            traza = None

    return render(
        request,
        "auditing/registros.html",
        {"pagina_dto": pagina_dto, "filtros": filtros, "traza": traza, "form": form},
    )

