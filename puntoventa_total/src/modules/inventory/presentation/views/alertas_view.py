"""Consolidado de alertas: stock minimo y vencimientos."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.modules.inventory.infrastructure.factories import construir_lote_repository, construir_stock_repository
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def alertas_view(request):
    stock_repo = construir_stock_repository()
    lote_repo = construir_lote_repository()
    umbral = PoliticaStock.umbral_minimo()
    return render(
        request,
        "inventory/alertas.html",
        {
            "bajo_minimo": stock_repo.productos_bajo_minimo(umbral),
            "por_vencer": lote_repo.lotes_por_vencer(PoliticaStock.dias_alerta_vencimiento()),
            "vencidos": lote_repo.lotes_vencidos(),
            "umbral": umbral,
        },
    )

