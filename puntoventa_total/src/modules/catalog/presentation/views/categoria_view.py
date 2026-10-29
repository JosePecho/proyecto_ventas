from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db import IntegrityError

from src.modules.catalog.application.use_cases.crear_categoria import CrearCategoria
from src.modules.catalog.domain.exceptions.producto_exceptions import CategoriaNoEncontrada, DomainException
from src.modules.catalog.infrastructure.factories import construir_categoria_repository
from src.modules.catalog.presentation.forms.categoria_form import CategoriaForm
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def categoria_view(request, categoria_id=None):
    repo = construir_categoria_repository()
    from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
    modelo = get_object_or_404(CategoriaModel, pk=categoria_id) if categoria_id else None
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            try:
                if modelo:
                    categoria = repo.buscar_por_id(categoria_id)
                    categoria.renombrar(form.cleaned_data["nombre"])
                    categoria.descripcion = form.cleaned_data["descripcion"]
                    repo.guardar(categoria)
                else:
                    from django.db import transaction
                    with transaction.atomic():
                        CrearCategoria(repo).ejecutar(form.cleaned_data["nombre"], form.cleaned_data.get("descripcion", ""))
                messages.success(request, "Categoria creada")
            except (DomainException, IntegrityError) as exc:
                messages.error(request, str(exc))
            else:
                return redirect("catalog:categorias")
    else:
        form = CategoriaForm(initial={"nombre": modelo.nombre, "descripcion": modelo.descripcion} if modelo else None)

    return render(request, "catalog/categoria_form.html", {"form": form, "categorias": repo.listar()})

