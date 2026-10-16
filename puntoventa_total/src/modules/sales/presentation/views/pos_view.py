"""Interfaz de punto de venta (carrito en sesion + busqueda por scanner)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.sales.application.use_cases.agregar_producto import AgregarProducto
from src.modules.sales.application.use_cases.crear_venta import CrearVenta
from src.modules.sales.application.use_cases.eliminar_producto import EliminarProducto
from src.modules.sales.application.use_cases.modificar_cantidad import ModificarCantidad
from src.modules.sales.domain.exceptions.venta_exceptions import VentaException
from src.modules.sales.infrastructure.factories import (
    construir_inventario_port,
    construir_promociones_port,
    construir_venta_repository,
)
from src.modules.sales.presentation.permissions.venta_permissions import (
    requiere_cajero,
    requiere_caja_abierta,
)


@login_required
@requiere_cajero
@requiere_caja_abierta
def pos_view(request):
    venta_id = request.session.get("venta_actual")
    if not venta_id:
        from src.modules.sales.application.dto.venta_input import CrearVentaDTO

        venta = CrearVenta(construir_venta_repository()).ejecutar(
            CrearVentaDTO(
                cajero_id=str(request.session.get("usuario_id", "")),
                turno_caja_id=request.session.get("turno_caja_id"),
            )
        )
        venta_id = venta.id
        request.session["venta_actual"] = venta_id

    contexto = {"venta_id": venta_id}
    return render(request, "pos/index.html", contexto)


@login_required
@requiere_cajero
def buscar_producto_pos(request):
    """Endpoint AJAX: escaner de codigo de barras o busqueda por texto."""
    termino = request.GET.get("q", "").strip()
    if not termino:
        return JsonResponse({"resultados": []})

    repo = construir_producto_repository()
    producto = repo.buscar_por_codigo_barras(termino)
    if producto:
        return JsonResponse(
            {
                "resultados": [
                    {
                        "id": str(producto.id),
                        "nombre": producto.nombre,
                        "precio": producto.precio.venta.a_float(),
                    }
                ]
            }
        )

    from src.modules.catalog.application.use_cases.buscar_producto import BuscarProducto

    resultados = BuscarProducto(repo).ejecutar(termino, limite=15)
    return JsonResponse(
        {
            "resultados": [
                {"id": r.id, "nombre": r.nombre, "precio": r.precio_venta, "codigo": r.codigo_barras}
                for r in resultados
            ]
        }
    )


@login_required
@requiere_cajero
def agregar_producto_pos(request, venta_id, producto_id, cantidad=1):
    if request.method != "POST":
        return redirect("sales:pos")
    producto = construir_producto_repository().buscar_por_id(producto_id)
    try:
        venta = AgregarProducto(
            construir_venta_repository(), construir_inventario_port(), construir_promociones_port()
        ).ejecutar(venta_id, producto, int(request.POST.get("cantidad", cantidad)))
    except VentaException as exc:
        messages.error(request, str(exc))
        return redirect("sales:pos")
    return JsonResponse({"total": venta.total, "lineas": len(venta.lineas)})


@login_required
@requiere_cajero
def modificar_cantidad_pos(request, venta_id, producto_id):
    cantidad = int(request.POST.get("cantidad", 1))
    venta = ModificarCantidad(construir_venta_repository()).ejecutar(venta_id, producto_id, cantidad)
    return JsonResponse({"total": venta.total})


@login_required
@requiere_cajero
def eliminar_producto_pos(request, venta_id, producto_id):
    venta = EliminarProducto(construir_venta_repository()).ejecutar(venta_id, producto_id)
    return JsonResponse({"total": venta.total, "lineas": len(venta.lineas)})

