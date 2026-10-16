from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.inventory.application.use_cases.consultar_kardex import ConsultarKardex
from src.modules.inventory.infrastructure.factories import construir_movimiento_repository
from src.modules.identity.presentation.permissions.role_required import role_required
from src.modules.inventory.presentation.forms.kardex_form import KardexForm


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def kardex_view(request):
    producto_id = request.GET.get("producto_id", "")
    form = KardexForm(request.GET)
    contexto = {"producto_id": producto_id, "pagina_dto": None, "form": form}
    if form.is_valid() and form.cleaned_data.get("producto_id"):
        datos = form.cleaned_data
        pagina_dto = ConsultarKardex(construir_movimiento_repository()).ejecutar(
            str(datos["producto_id"].pk),
            desde=request.GET.get("desde") or None,
            hasta=request.GET.get("hasta") or None,
            pagina=datos.get("pagina") or 1,
        )
        contexto["pagina_dto"] = pagina_dto
    return render(request, "inventory/kardex.html", contexto)

