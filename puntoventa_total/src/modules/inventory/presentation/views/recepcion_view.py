"""Recepcion de mercaderia (ingreso de lote)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
from src.modules.inventory.domain.exceptions.stock_exceptions import StockException
from src.modules.inventory.infrastructure.factories import (
    construir_lote_repository,
    construir_movimiento_repository,
    construir_stock_repository,
)
from src.modules.inventory.presentation.forms.recepcion_form import RecepcionForm
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def recepcion_view(request):
    if request.method == "POST":
        form = RecepcionForm(request.POST)
        if form.is_valid():
            try:
                lote = RecibirMercaderia(
                    construir_stock_repository(),
                    construir_lote_repository(),
                    construir_movimiento_repository(),
                    uow=transaction.atomic(),
                ).ejecutar(
                    RecepcionLoteDTO(
                        producto_id=form.cleaned_data["producto_id"],
                        numero_lote=form.cleaned_data["numero_lote"],
                        cantidad=form.cleaned_data["cantidad"],
                        costo_unitario=form.cleaned_data["costo_unitario"],
                        proveedor=form.cleaned_data.get("proveedor", ""),
                        fecha_vencimiento=form.cleaned_data.get("fecha_vencimiento"),
                    ),
                    usuario_id=str(request.session.get("usuario_id", "")),
                )
            except StockException as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, f"Lote {lote.numero_lote} registrado")
                return redirect("inventory:inventario")
    else:
        form = RecepcionForm()

    return render(request, "inventory/recepcion.html", {"form": form})

