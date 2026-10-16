"""Administracion de productos (requiere rol GERENTE/ADMINISTRADOR)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from src.modules.catalog.application.dto.producto_input import ActualizarProductoDTO, ProductoInputDTO
from src.modules.catalog.application.use_cases.actualizar_producto import ActualizarProducto
from src.modules.catalog.application.use_cases.crear_producto import CrearProducto
from src.modules.catalog.application.use_cases.descontinuar_producto import DescontinuarProducto
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoException
from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.catalog.presentation.forms.producto_form import ProductoForm
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def productos_admin(request):
    productos = construir_producto_repository().listar(incluir_inactivos=True)
    return render(request, "catalog/productos_admin.html", {"productos": productos})


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def producto_form_view(request, producto_id=None):
    repo = construir_producto_repository()
    producto = None
    if producto_id:
        producto = get_object_or_404(repo.listar(incluir_inactivos=True), pk=producto_id)

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                if producto is None:
                    CrearProducto(repo).ejecutar(
                        ProductoInputDTO(
                            nombre=form.cleaned_data["nombre"],
                            descripcion=form.cleaned_data.get("descripcion", ""),
                            codigo_barras=form.cleaned_data["codigo_barras"],
                            costo=form.cleaned_data["costo"],
                            precio_venta=form.cleaned_data["precio_venta"],
                            categoria_id=form.cleaned_data.get("categoria_id"),
                        )
                    )
                    messages.success(request, "Producto creado")
                else:
                    ActualizarProducto(repo).ejecutar(
                        ActualizarProductoDTO(
                            producto_id=str(producto.id),
                            nombre=form.cleaned_data["nombre"],
                            descripcion=form.cleaned_data.get("descripcion", ""),
                            costo=form.cleaned_data["costo"],
                            precio_venta=form.cleaned_data["precio_venta"],
                            categoria_id=form.cleaned_data.get("categoria_id"),
                        )
                    )
                    messages.success(request, "Producto actualizado")
            except ProductoException as exc:
                messages.error(request, str(exc))
            else:
                return redirect("catalog:productos_admin")
    else:
        form = ProductoForm()

    return render(request, "catalog/producto_form.html", {"form": form, "producto": producto})


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def producto_descontinuar_view(request, producto_id):
    if request.method == "POST":
        try:
            DescontinuarProducto(construir_producto_repository()).ejecutar(producto_id)
            messages.success(request, "Producto descontinuado")
        except ProductoException as exc:
            messages.error(request, str(exc))
    return redirect("catalog:productos_admin")

