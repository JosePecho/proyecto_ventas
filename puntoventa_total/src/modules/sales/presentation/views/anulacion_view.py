from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from src.modules.sales.application.use_cases.anular_venta import AnularVenta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaException
from src.modules.sales.infrastructure.factories import (
    construir_auditoria_port,
    construir_inventario_port,
    construir_venta_repository,
)
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.presentation.permissions.venta_permissions import requiere_gerente_anulacion


@login_required
@requiere_gerente_anulacion
def anulacion_view(request, venta_id):
    venta = get_object_or_404(VentaModel, pk=venta_id)

    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        if not motivo:
            messages.error(request, "Debe indicar el motivo de anulacion")
        else:
            try:
                AnularVenta(
                    construir_venta_repository(),
                    construir_inventario_port(),
                    construir_auditoria_port(),
                    uow=transaction.atomic(),
                ).ejecutar(venta_id, motivo, str(request.session.get("usuario_id", "")))
            except VentaException as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Venta anulada y stock devuelto")
                return redirect("sales:ventas")

    return render(request, "pos/pago.html", {"venta": venta, "anulacion": True})

