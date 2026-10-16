"""Seguimiento publico por numero de pedido."""
from __future__ import annotations

from django.shortcuts import render

from src.modules.orders.application.use_cases.consultar_estado import ConsultarEstado
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.modules.orders.infrastructure.factories import construir_pedido_repository

ESTADOS_FLUJO = ["BORRADOR", "CONFIRMADO", "EN_PREPARACION", "LISTO", "ENTREGADO"]


def seguimiento_view(request):
    numero = request.GET.get("numero", "").strip()
    contexto = {"numero": numero, "pedido": None, "error": None, "pasos": ESTADOS_FLUJO}
    if numero:
        try:
            pedido = ConsultarEstado(construir_pedido_repository()).por_numero(numero)
            contexto["pedido"] = pedido
            contexto["paso_actual"] = ESTADOS_FLUJO.index(pedido.estado) if pedido.estado in ESTADOS_FLUJO else -1
        except PedidoException as exc:
            contexto["error"] = str(exc)
    return render(request, "orders/seguimiento.html", contexto)

