"""Listado de existencias con alertas de stock minimo."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.modules.inventory.infrastructure.factories import construir_stock_repository
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def inventario_view(request):
    existencias = construir_stock_repository().productos_bajo_minimo(10**9)
    umbral = PoliticaStock.umbral_minimo()
    for item in existencias:
        item["bajo_minimo"] = item["disponible"] <= umbral
    return render(
        request,
        "inventory/index.html",
        {"existencias": existencias, "umbral": umbral},
    )

