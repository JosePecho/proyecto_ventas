from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from src.modules.inventory.application.use_cases.registrar_merma import RegistrarMerma
from src.modules.inventory.domain.exceptions.stock_exceptions import StockException
from src.modules.inventory.infrastructure.factories import (
    construir_lote_repository,
    construir_movimiento_repository,
    construir_stock_repository,
)
from src.modules.identity.presentation.permissions.role_required import role_required
from src.modules.inventory.presentation.forms.merma_form import MermaForm
from src.shared.domain.exceptions.validation_exception import ValidationException


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def merma_view(request):
    if request.method == "POST":
        form = MermaForm(request.POST)
        if not form.is_valid():
            return render(request, "inventory/mermas.html", {"form": form})
        datos = form.cleaned_data
        try:
            RegistrarMerma(
                construir_stock_repository(),
                construir_lote_repository(),
                construir_movimiento_repository(),
                uow=transaction.atomic(),
            ).ejecutar(
                str(datos["producto_id"].pk),
                datos["cantidad"],
                datos["motivo"],
                usuario_id=str(request.session.get("usuario_id", "")),
                lote_id=str(datos["lote_id"].pk) if datos.get("lote_id") else None,
                observacion=datos.get("observacion", ""),
            )
        except (StockException, ValidationException, ValueError) as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Merma registrada")
            return redirect("inventory:mermas")

    else:
        form = MermaForm()
    return render(request, "inventory/mermas.html", {"form": form})

