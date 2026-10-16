from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from src.modules.orders.application.use_cases.confirmar_pedido import ConfirmarPedido
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.modules.orders.infrastructure.factories import construir_inventario_port, construir_pedido_repository
from src.modules.orders.presentation.forms.pedido_form import PedidoForm


@login_required
def checkout_view(request):
    pedido_id = request.session.get("pedido_web")
    if not pedido_id:
        messages.warning(request, "Su carrito esta vacio")
        return redirect("orders:carrito")

    if request.method == "POST":
        form = PedidoForm(request.POST)
        if form.is_valid():
            try:
                ConfirmarPedido(
                    construir_pedido_repository(), construir_inventario_port(), uow=transaction.atomic()
                ).ejecutar(pedido_id)
            except PedidoException as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Pedido confirmado. Le avisaremos cuando este listo.")
                return redirect("orders:confirmacion", pedido_id=pedido_id)
    else:
        form = PedidoForm(initial={"cliente_nombre": request.user.get_full_name()})

    return render(request, "orders/checkout.html", {"form": form, "pedido_id": pedido_id})

