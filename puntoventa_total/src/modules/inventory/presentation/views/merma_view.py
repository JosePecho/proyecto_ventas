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


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def merma_view(request):
    if request.method == "POST":
        producto_id = request.POST.get("producto_id", "")
        motivo = request.POST.get("motivo", "OTRO")
        observacion = request.POST.get("observacion", "")
        try:
            cantidad = int(request.POST.get("cantidad", 0))
            RegistrarMerma(
                construir_stock_repository(),
                construir_lote_repository(),
                construir_movimiento_repository(),
                uow=transaction.atomic(),
            ).ejecutar(
                producto_id,
                cantidad,
                motivo,
                usuario_id=str(request.session.get("usuario_id", "")),
                lote_id=request.POST.get("lote_id") or None,
                observacion=observacion,
            )
        except (StockException, ValueError) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Merma registrada")
            return redirect("inventory:mermas")

    from src.modules.inventory.domain.enums.motivo_merma import MotivoMerma

    return render(request, "inventory/mermas.html", {"motivos": MotivoMerma.opciones()})

