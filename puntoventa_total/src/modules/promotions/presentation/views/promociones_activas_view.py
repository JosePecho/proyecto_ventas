"""Vitrina de promociones vigentes (cliente + POS)."""
from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import render

from src.modules.promotions.infrastructure.factories import construir_promocion_repository


def promociones_activas_view(request):
    activas = [p for p in construir_promocion_repository().listar_activas() if p.esta_vigente()]
    if request.headers.get("Accept") == "application/json":
        return JsonResponse(
            {"promociones": [{"id": str(p.id), "nombre": p.nombre, "tipo": p.tipo.value} for p in activas]}
        )
    return render(request, "promotions/index.html", {"promociones": activas, "solo_activas": True})

