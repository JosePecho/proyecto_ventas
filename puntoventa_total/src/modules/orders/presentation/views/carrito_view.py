"""Carrito web del cliente (sesion + reservas de stock)."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.db import transaction
from src.modules.orders.presentation.ownership import pedido_propio
from src.modules.orders.application.dto.pedido_output import PedidoOutputDTO
from src.shared.domain.exceptions.domain_exception import DomainException

from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.orders.application.use_cases.agregar_producto_pedido import AgregarProductoPedido
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.modules.orders.infrastructure.factories import construir_inventario_port, construir_pedido_repository


@login_required
def carrito_view(request):
    pedido_id = request.session.get("pedido_web")
    contexto = {"pedido_id": pedido_id, "lineas": [], "total": 0.0}
    if pedido_id:
        modelo = pedido_propio(request, pedido_id)
        if modelo.estado != "BORRADOR":
            request.session.pop("pedido_web", None)
            return redirect("orders:detalle", pedido_id=pedido_id)
        try:
            pedido = PedidoOutputDTO.desde_agregado(construir_pedido_repository().buscar_por_id(pedido_id))
            contexto.update({"lineas": pedido.lineas, "total": pedido.total, "estado": pedido.estado})
        except PedidoException:
            request.session.pop("pedido_web", None)
    return render(request, "orders/carrito.html", contexto)


@login_required
@transaction.atomic
def agregar_al_carrito(request, producto_id):
    if request.method != "POST":
        return redirect("catalog:catalogo")

    producto = construir_producto_repository().buscar_por_id(producto_id)
    if producto is None:
        messages.error(request, "Producto no encontrado")
        return redirect("catalog:catalogo")

    pedido_id = request.session.get("pedido_web")
    if pedido_id:
        modelo = pedido_propio(request, pedido_id, lock=True)
        if modelo.estado != "BORRADOR":
            pedido_id = None
    if not pedido_id:
        from src.modules.orders.application.use_cases.crear_pedido import CrearPedido
        from src.modules.orders.application.dto.pedido_input import CrearPedidoDTO

        from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
        from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
        from django.shortcuts import get_object_or_404
        usuario = get_object_or_404(UsuarioModel, pk=request.session.get("usuario_id"))
        cliente = ClienteModel.objects.filter(usuario_id=usuario.id).first()
        creado = CrearPedido(construir_pedido_repository()).ejecutar(
            CrearPedidoDTO(cliente_nombre=usuario.nombre_completo, cliente_id=str(usuario.id),
                           cliente_email=usuario.email,
                           cliente_dni=cliente.dni if cliente else None,
                           cliente_telefono=cliente.telefono if cliente else "")
        )
        pedido_id = creado.id
        request.session["pedido_web"] = pedido_id

    try:
        AgregarProductoPedido(construir_pedido_repository(), construir_inventario_port()).ejecutar(
            pedido_id, producto, int(request.POST.get("cantidad", 1))
        )
    except (DomainException, ValueError) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"{producto.nombre} agregado al carrito")
    return redirect("orders:carrito")

