from django.http import Http404
from django.shortcuts import get_object_or_404

from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel


def pedido_propio(request, pedido_id, *, lock=False):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        raise Http404
    qs = PedidoModel.objects.filter(cliente_id=usuario_id)
    if lock:
        qs = qs.select_for_update()
    return get_object_or_404(qs, pk=pedido_id)
