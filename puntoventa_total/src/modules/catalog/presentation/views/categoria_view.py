from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from src.modules.catalog.application.use_cases.crear_categoria import CrearCategoria
from src.modules.catalog.domain.exceptions.producto_exceptions import CategoriaNoEncontrada, DomainException
from src.modules.catalog.infrastructure.factories import construir_categoria_repository
from src.modules.catalog.presentation.forms.categoria_form import CategoriaForm
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def categoria_view(request):
    repo = construir_categoria_repository()
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            try:
                CrearCategoria(repo).ejecutar(
                    form.cleaned_data["nombre"], form.cleaned_data.get("descripcion", "")
                )
                messages.success(request, "Categoria creada")
            except (DomainException, CategoriaNoEncontrada) as exc:
                messages.error(request, str(exc))
            else:
                return redirect("catalog:categorias")
    else:
        form = CategoriaForm()

    return render(request, "catalog/categoria_form.html", {"form": form, "categorias": repo.listar()})

