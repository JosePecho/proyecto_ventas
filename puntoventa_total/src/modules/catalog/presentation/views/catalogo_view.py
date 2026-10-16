"""Vitrina publica del catalogo (cliente)."""
from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from django.core.files.storage import default_storage
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from src.modules.catalog.application.use_cases.listar_productos import ListarProductos
from src.modules.catalog.infrastructure.factories import (
    construir_categoria_repository,
    construir_producto_repository,
    construir_disponibilidad_port,
)


@never_cache
def catalogo_view(request):
    termino = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria") or None
    try:
        pagina = int(request.GET.get("pagina", "1"))
    except ValueError:
        pagina = 1
    if categoria_id:
        try:
            categoria_id = str(UUID(categoria_id))
        except ValueError:
            raise Http404("Categoria no encontrada")

    pagina_dto = ListarProductos(construir_producto_repository()).ejecutar(
        pagina=pagina, termino=termino or None, categoria_id=categoria_id,
    )
    stocks = construir_disponibilidad_port().stock_disponible_lote([p.id for p in pagina_dto.items])
    items = [replace(p, stock_disponible=stocks.get(p.id, 0),
                     imagen=default_storage.url(p.imagen) if p.imagen else "") for p in pagina_dto.items]

    categorias = construir_categoria_repository().listar()
    filtros = request.GET.copy()
    filtros.pop("pagina", None)
    contexto = {**pagina_dto.a_contexto(), "items": items, "categorias": categorias,
                "termino": termino, "categoria_actual": categoria_id or "",
                "filtros": filtros.urlencode()}
    return render(request, "catalog/index.html", contexto)

