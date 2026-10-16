"""Cobro de la venta actual."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.exceptions.venta_exceptions import VentaException
from src.modules.sales.infrastructure.factories import (
    construir_auditoria_port,
    construir_inventario_port,
    construir_venta_repository,
)
from src.modules.sales.presentation.forms.pago_form import PagoForm
from src.modules.sales.presentation.permissions.venta_permissions import (
    requiere_caja_abierta,
    requiere_cajero,
)


@login_required
@requiere_cajero
@requiere_caja_abierta
def pago_view(request, venta_id):
    if request.method == "POST":
        form = PagoForm(request.POST)
        if form.is_valid():
            from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO

            try:
                resultado = ProcesarPago(
                    construir_venta_repository(),
                    construir_inventario_port(),
                    construir_auditoria_port(),
                    uow=transaction.atomic(),
                ).ejecutar(
                    ProcesarPagoDTO(
                        venta_id=venta_id,
                        metodo=form.cleaned_data["metodo"],
                        monto=form.cleaned_data["monto"],
                        monto_entregado=form.cleaned_data.get("monto_entregado"),
                        referencia=form.cleaned_data.get("referencia", ""),
                    )
                )
            except VentaException as exc:
                messages.error(request, str(exc))
            else:
                request.session.pop("venta_actual", None)
                if resultado["estado"] == "PAGADA":
                    messages.success(request, f"Venta cobrada. Vuelto: {resultado['vuelto']:.2f}")
                    return redirect("sales:ticket", venta_id=venta_id)
                messages.warning(request, f"Pago parcial. Saldo pendiente: {resultado['saldo']:.2f}")
                return redirect("sales:pago", venta_id=venta_id)
    else:
        form = PagoForm()

    return render(request, "pos/pago.html", {"form": form, "venta_id": venta_id})

