"""Administracion de productos (requiere rol GERENTE/ADMINISTRADOR)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render

from src.modules.catalog.application.dto.producto_input import ActualizarProductoDTO, ProductoInputDTO
from src.modules.catalog.application.use_cases.actualizar_producto import ActualizarProducto
from src.modules.catalog.application.use_cases.crear_producto import CrearProducto
from src.modules.catalog.application.use_cases.descontinuar_producto import DescontinuarProducto
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoException
from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.catalog.presentation.forms.producto_form import ProductoForm
from src.modules.identity.presentation.permissions.role_required import role_required
from src.shared.domain.exceptions.validation_exception import ValidationException


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def productos_admin(request):
    productos = construir_producto_repository().listar(incluir_inactivos=True)
    return render(request, "catalog/productos_admin.html", {"productos": productos})


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "ALMACENERO")
def producto_form_view(request, producto_id=None):
    repo = construir_producto_repository()
    producto = None
    if producto_id:
        producto = repo.buscar_por_id(producto_id)
        if producto is None:
            raise Http404("Producto no encontrado")

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    return _guardar_producto(request, repo, producto, form)
            except (ProductoException, ValidationException, ValueError) as exc:
                form.add_error(None, str(exc))
    else:
        initial = {}
        if producto:
            initial = {
                "nombre": producto.nombre, "descripcion": producto.descripcion,
                "codigo_barras": str(producto.codigo_barras), "costo": producto.precio.costo.valor,
                "precio_venta": producto.precio.venta.valor, "categoria_id": producto.categoria_id,
                "stock_minimo": producto.stock_minimo, "fecha_vencimiento": producto.fecha_vencimiento,
            }
        form = ProductoForm(initial=initial)

    return render(request, "catalog/producto_form.html", {"form": form, "producto": producto})


def _guardar_producto(request, repo, producto, form):
    datos = dict(
        nombre=form.cleaned_data["nombre"],
        descripcion=form.cleaned_data.get("descripcion", ""),
        codigo_barras=form.cleaned_data["codigo_barras"],
        costo=form.cleaned_data["costo"],
        precio_venta=form.cleaned_data["precio_venta"],
        categoria_id=form.cleaned_data["categoria_id"],
        stock_minimo=form.cleaned_data["stock_minimo"],
        fecha_vencimiento=form.cleaned_data.get("fecha_vencimiento"),
    )
    if producto is None:
        resultado = CrearProducto(repo).ejecutar(ProductoInputDTO(**datos))
    else:
        resultado = ActualizarProducto(repo).ejecutar(
            ActualizarProductoDTO(**datos, producto_id=str(producto.id), actualizar_vencimiento=True)
        )
    if form.cleaned_data.get("imagen"):
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
        modelo = ProductoModel.objects.get(pk=resultado.id)
        modelo.imagen = form.cleaned_data["imagen"]
        modelo.save(update_fields=["imagen", "fecha_actualizacion"])
    messages.success(request, "Producto creado" if producto is None else "Producto actualizado")
    return redirect("catalog:productos_admin")


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

