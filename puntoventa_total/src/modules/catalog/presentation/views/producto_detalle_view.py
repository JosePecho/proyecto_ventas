from __future__ import annotations

from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

from src.modules.catalog.application.use_cases.consultar_disponibilidad import ConsultarDisponibilidad
from src.modules.catalog.infrastructure.factories import (
    construir_disponibilidad_port,
    construir_producto_repository,
)
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel


@never_cache
def producto_detalle_view(request, producto_id):
    producto = get_object_or_404(ProductoModel.objects.select_related("categoria"), pk=producto_id, activo=True, estado="ACTIVO")
    disponibilidad = ConsultarDisponibilidad(
        construir_producto_repository(), construir_disponibilidad_port()
    ).ejecutar(str(producto.id))
    return render(
        request,
        "catalog/producto_detalle.html",
        {"producto": producto, "disponibilidad": disponibilidad},
    )

