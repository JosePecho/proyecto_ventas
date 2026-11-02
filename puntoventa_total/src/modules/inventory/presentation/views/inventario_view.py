"""Listado de existencias con alertas de stock minimo."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.identity.presentation.permissions.role_required import role_required
from src.modules.inventory.infrastructure.factories import construir_stock_repository


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def inventario_view(request):
    existencias = construir_stock_repository().listar_existencias()
    return render(
        request,
        "inventory/index.html",
        {"existencias": existencias},
    )

