"""Carrito web del cliente (sesion + reservas de stock)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.orders.application.use_cases.agregar_producto_pedido import AgregarProductoPedido
from src.modules.orders.application.use_cases.consultar_estado import ConsultarEstado
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.modules.orders.infrastructure.factories import construir_inventario_port, construir_pedido_repository


@login_required
def carrito_view(request):
    pedido_id = request.session.get("pedido_web")
    contexto = {"pedido_id": pedido_id, "lineas": [], "total": 0.0}
    if pedido_id:
        try:
            pedido = ConsultarEstado(construir_pedido_repository()).por_numero(pedido_id)
            contexto.update({"lineas": pedido.lineas, "total": pedido.total, "estado": pedido.estado})
        except PedidoException:
            request.session.pop("pedido_web", None)
    return render(request, "orders/carrito.html", contexto)


@login_required
def agregar_al_carrito(request, producto_id):
    if request.method != "POST":
        return redirect("catalog:catalogo")

    producto = construir_producto_repository().buscar_por_id(producto_id)
    if producto is None:
        messages.error(request, "Producto no encontrado")
        return redirect("catalog:catalogo")

    pedido_id = request.session.get("pedido_web")
    if not pedido_id:
        from src.modules.orders.application.use_cases.crear_pedido import CrearPedido
        from src.modules.orders.application.dto.pedido_input import CrearPedidoDTO

        creado = CrearPedido(construir_pedido_repository()).ejecutar(
            CrearPedidoDTO(cliente_nombre=request.user.get_full_name() or request.user.username)
        )
        pedido_id = creado.id
        request.session["pedido_web"] = pedido_id

    try:
        AgregarProductoPedido(construir_pedido_repository(), construir_inventario_port()).ejecutar(
            pedido_id, producto, int(request.POST.get("cantidad", 1))
        )
    except (PedidoException, Exception) as exc:  # noqa: BLE001 - se muestra al usuario
        messages.error(request, str(exc))
    else:
        messages.success(request, f"{producto.nombre} agregado al carrito")
    return redirect("orders:carrito")

