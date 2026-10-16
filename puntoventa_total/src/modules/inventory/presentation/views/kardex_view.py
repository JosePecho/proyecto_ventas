from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.inventory.application.use_cases.consultar_kardex import ConsultarKardex
from src.modules.inventory.infrastructure.factories import construir_movimiento_repository
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def kardex_view(request):
    producto_id = request.GET.get("producto_id", "")
    pagina = int(request.GET.get("pagina", 1) or 1)
    contexto = {"producto_id": producto_id, "pagina_dto": None}
    if producto_id:
        pagina_dto = ConsultarKardex(construir_movimiento_repository()).ejecutar(
            producto_id,
            desde=request.GET.get("desde") or None,
            hasta=request.GET.get("hasta") or None,
            pagina=pagina,
        )
        contexto["pagina_dto"] = pagina_dto
    return render(request, "inventory/kardex.html", contexto)

