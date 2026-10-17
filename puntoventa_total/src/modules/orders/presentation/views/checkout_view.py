from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from src.modules.orders.application.use_cases.confirmar_pedido import ConfirmarPedido
from src.modules.orders.infrastructure.factories import construir_inventario_port, construir_pedido_repository
from src.modules.orders.presentation.forms.pedido_form import PedidoForm
from src.modules.orders.presentation.ownership import pedido_propio
from src.shared.domain.exceptions.domain_exception import DomainException


@login_required
def checkout_view(request):
    pedido_id = request.session.get("pedido_web")
    if not pedido_id:
        messages.warning(request, "Su carrito esta vacio")
        return redirect("orders:carrito")
    modelo = pedido_propio(request, pedido_id)
    if modelo.estado != "BORRADOR":
        return redirect("orders:detalle", pedido_id=pedido_id)

    if request.method == "POST":
        form = PedidoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    modelo = pedido_propio(request, pedido_id, lock=True)
                    repo = construir_pedido_repository()
                    agregado = repo.buscar_por_id(pedido_id)
                    agregado.pedido.cliente_nombre = form.cleaned_data["cliente_nombre"]
                    agregado.pedido.cliente_dni = form.cleaned_data["cliente_dni"] or None
                    agregado.pedido.cliente_telefono = form.cleaned_data["cliente_telefono"]
                    agregado.pedido.observaciones = form.cleaned_data["observaciones"]
                    agregado.pedido.asignar_hora_recojo(form.cleaned_data["hora_recojo"])
                    repo.guardar(agregado)
                    ConfirmarPedido(repo, construir_inventario_port()).ejecutar(pedido_id)
            except DomainException as exc:
                messages.error(request, str(exc))
            else:
                request.session.pop("pedido_web", None)
                messages.success(request, "Pedido confirmado. Le avisaremos cuando este listo.")
                return redirect("orders:confirmacion", pedido_id=pedido_id)
    else:
        form = PedidoForm(initial={"cliente_nombre": modelo.cliente_nombre,
                                   "cliente_dni": modelo.cliente_dni,
                                   "cliente_telefono": modelo.cliente_telefono,
                                   "modalidad": "RECOJO"})

    return render(request, "orders/checkout.html", {"form": form, "pedido_id": pedido_id})

