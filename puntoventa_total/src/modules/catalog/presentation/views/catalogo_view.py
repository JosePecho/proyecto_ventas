"""Vitrina publica del catalogo (cliente)."""
from __future__ import annotations

from django.shortcuts import render

from src.modules.catalog.application.use_cases.filtrar_por_categoria import FiltrarPorCategoria
from src.modules.catalog.application.use_cases.listar_productos import ListarProductos
from src.modules.catalog.infrastructure.factories import (
    construir_categoria_repository,
    construir_producto_repository,
)


def catalogo_view(request):
    termino = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria") or None
    pagina = int(request.GET.get("pagina", 1) or 1)

    if categoria_id:
        pagina_dto = FiltrarPorCategoria(construir_producto_repository()).ejecutar(categoria_id, pagina)
    else:
        pagina_dto = ListarProductos(construir_producto_repository()).ejecutar(
            pagina=pagina, termino=termino or None
        )

    categorias = construir_categoria_repository().listar()
    contexto = {**pagina_dto.a_contexto(), "categorias": categorias, "termino": termino}
    return render(request, "catalog/index.html", contexto)

