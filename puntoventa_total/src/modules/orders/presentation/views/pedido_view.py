"""Detalle de pedidos del cliente y panel de cocina."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from src.modules.orders.application.use_cases.consultar_estado import ConsultarEstado
from src.modules.orders.infrastructure.factories import construir_pedido_repository
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
def mis_pedidos_view(request):
    pedidos = ConsultarEstado(construir_pedido_repository()).del_cliente(
        str(request.session.get("usuario_id", ""))
    )
    return render(request, "orders/mis_pedidos.html", {"pedidos": pedidos})


@login_required
def detalle_pedido_view(request, pedido_id):
    get_object_or_404(PedidoModel, pk=pedido_id)
    pedido = ConsultarEstado(construir_pedido_repository()).por_numero(
        str(PedidoModel.objects.get(pk=pedido_id).numero)
    )
    return render(request, "orders/detalle_pedido.html", {"pedido": pedido})


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
def pedidos_cocina_view(request):
    return render(
        request,
        "orders/mis_pedidos.html",
        {"pedidos": ConsultarEstado(construir_pedido_repository()).en_cocina(), "cocina": True},
    )

