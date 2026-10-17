"""Detalle de pedidos del cliente y panel de cocina."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from src.modules.orders.application.use_cases.consultar_estado import ConsultarEstado
from src.modules.orders.infrastructure.factories import construir_pedido_repository
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.identity.presentation.permissions.role_required import role_required
from src.modules.orders.presentation.ownership import pedido_propio


@login_required
def mis_pedidos_view(request):
    if not request.session.get("usuario_id"):
        from django.http import Http404
        raise Http404
    pedidos = ConsultarEstado(construir_pedido_repository()).del_cliente(
        str(request.session.get("usuario_id", ""))
    )
    return render(request, "orders/mis_pedidos.html", {"pedidos": pedidos})


@login_required
def detalle_pedido_view(request, pedido_id):
    if request.session.get("rol") in ("ADMINISTRADOR", "GERENTE", "CAJERO"):
        modelo = get_object_or_404(PedidoModel, pk=pedido_id)
    else:
        modelo = pedido_propio(request, pedido_id)
    pedido = ConsultarEstado(construir_pedido_repository()).por_numero(
        modelo.numero
    )
    return render(request, "orders/detalle_pedido.html", {"pedido": pedido})


@login_required
def cancelar_pedido_view(request, pedido_id):
    from django.db import transaction
    from django.shortcuts import redirect
    from django.http import HttpResponseNotAllowed
    from django.contrib import messages
    from src.modules.orders.application.use_cases.cancelar_pedido import CancelarPedido
    from src.modules.orders.infrastructure.factories import construir_inventario_port
    from src.shared.domain.exceptions.domain_exception import DomainException
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        with transaction.atomic():
            modelo = pedido_propio(request, pedido_id, lock=True)
            if modelo.estado != "CONFIRMADO":
                from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
                raise PedidoException("Solo puedes cancelar un pedido Pendiente")
            CancelarPedido(construir_pedido_repository(), construir_inventario_port()).ejecutar(
                str(pedido_id), "Cancelado por el cliente", str(request.session["usuario_id"])
            )
    except DomainException as exc:
        messages.error(request, str(exc))
    return redirect("orders:detalle", pedido_id=pedido_id)


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
def cambiar_estado_view(request, pedido_id):
    from django.db import transaction
    from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
    from django.shortcuts import redirect
    from django.contrib import messages
    from src.shared.domain.exceptions.domain_exception import DomainException
    from src.modules.orders.application.use_cases.preparar_pedido import PrepararPedido
    from src.modules.orders.application.use_cases.marcar_pedido_listo import MarcarPedidoListo
    from src.modules.orders.application.use_cases.entregar_pedido import EntregarPedido
    from src.modules.orders.infrastructure.factories import construir_inventario_port
    from src.modules.orders.infrastructure.tasks.enviar_notificacion_pedido import run
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    estado = request.POST.get("estado")
    if estado not in ("EN_PREPARACION", "LISTO", "ENTREGADO"):
        return HttpResponseBadRequest("Estado no válido")
    try:
        with transaction.atomic():
            get_object_or_404(PedidoModel.objects.select_for_update(), pk=pedido_id)
            repo = construir_pedido_repository()
            if estado == "EN_PREPARACION":
                PrepararPedido(repo).ejecutar(str(pedido_id))
            elif estado == "LISTO":
                MarcarPedidoListo(repo).ejecutar(str(pedido_id))
                transaction.on_commit(lambda: run.delay(str(pedido_id)), robust=True)
            else:
                EntregarPedido(repo, construir_inventario_port()).ejecutar(
                    str(pedido_id), str(request.session["usuario_id"])
                )
    except DomainException as exc:
        messages.error(request, str(exc))
    return redirect("orders:detalle", pedido_id=pedido_id)


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
def pedidos_cocina_view(request):
    return render(
        request,
        "orders/mis_pedidos.html",
        {"pedidos": ConsultarEstado(construir_pedido_repository()).en_cocina(), "cocina": True},
    )

