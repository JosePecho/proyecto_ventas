"""Consolidado de alertas: stock minimo y vencimientos."""
from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.factories import construir_lote_repository, construir_stock_repository
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def alertas_view(request):
    stock_repo = construir_stock_repository()
    lote_repo = construir_lote_repository()
    hoy = date.today()
    productos = {str(p.id): p for p in ProductoModel.objects.filter(activo=True)}
    por_vencer = list(lote_repo.lotes_por_vencer(30))
    for lote in por_vencer:
        producto = productos.get(str(lote.producto_id))
        lote.producto_nombre = producto.nombre if producto else str(lote.producto_id)
    # El vencimiento del catalogo cubre productos aun sin recepciones.
    ids_con_lotes = {str(pk) for pk in LoteModel.objects.filter(activo=True).values_list("producto_id", flat=True)}
    for p in productos.values():
        if (str(p.id) not in ids_con_lotes and p.fecha_vencimiento
                and hoy <= p.fecha_vencimiento <= hoy + timedelta(days=30)):
            por_vencer.append({
                "producto_nombre": p.nombre, "numero_lote": "Sin lote",
                "fecha_vencimiento": p.fecha_vencimiento,
                "dias_para_vencer": (p.fecha_vencimiento - hoy).days,
            })
    return render(
        request,
        "inventory/alertas.html",
        {
            "bajo_minimo": stock_repo.productos_bajo_minimo(),
            "por_vencer": por_vencer,
            "vencidos": lote_repo.lotes_vencidos(),
        },
    )

