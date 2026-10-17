"""Interfaz de punto de venta (carrito en sesion + busqueda por scanner)."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from src.shared.domain.exceptions.domain_exception import DomainException
from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.presentation.permissions.venta_permissions import venta_propia

from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.sales.application.use_cases.agregar_producto import AgregarProducto
from src.modules.sales.application.use_cases.crear_venta import CrearVenta
from src.modules.sales.application.use_cases.eliminar_producto import EliminarProducto
from src.modules.sales.application.use_cases.modificar_cantidad import ModificarCantidad
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
    repo = construir_venta_repository()
    agregado = repo.buscar_por_id(venta_id) if venta_id else None
    if agregado and (agregado.venta.estado.value != "BORRADOR" or
                     agregado.venta.cajero_id != str(request.session.get("usuario_id", ""))):
        agregado = None
    if agregado is None:
        from src.modules.sales.application.dto.venta_input import CrearVentaDTO

        venta = CrearVenta(construir_venta_repository()).ejecutar(
            CrearVentaDTO(
                cajero_id=str(request.session.get("usuario_id", "")),
                turno_caja_id=request.session.get("turno_caja_id"),
            )
        )
        venta_id = venta.id
        request.session["venta_actual"] = venta_id
        agregado = repo.buscar_por_id(venta_id)

    contexto = {"venta_id": venta_id, "venta": VentaOutputDTO.desde_agregado(agregado)}
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
@require_POST
@venta_propia
def agregar_producto_pos(request, venta_id, producto_id, cantidad=1):
    producto = construir_producto_repository().buscar_por_id(producto_id)
    try:
        venta = AgregarProducto(
            construir_venta_repository(), construir_inventario_port(), construir_promociones_port()
        ).ejecutar(venta_id, producto, int(request.POST.get("cantidad", cantidad)))
    except (DomainException, ValueError, TypeError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"total": venta.total, "lineas": len(venta.lineas)})


@login_required
@requiere_cajero
@require_POST
@venta_propia
def modificar_cantidad_pos(request, venta_id, producto_id):
    try:
        cantidad = int(request.POST.get("cantidad", 1))
        venta = ModificarCantidad(
            construir_venta_repository(), construir_inventario_port(), construir_promociones_port()
        ).ejecutar(venta_id, str(producto_id), cantidad)
    except (DomainException, ValueError, TypeError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"total": venta.total})


@login_required
@requiere_cajero
@require_POST
@venta_propia
def eliminar_producto_pos(request, venta_id, producto_id):
    try:
        venta = EliminarProducto(construir_venta_repository()).ejecutar(venta_id, str(producto_id))
    except DomainException as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"total": venta.total, "lineas": len(venta.lineas)})

