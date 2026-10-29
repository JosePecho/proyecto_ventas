"""Unidades que el cliente aun puede agregar a su carrito."""
from src.modules.orders.infrastructure.persistence.django_models.detalle_pedido_model import DetallePedidoModel


def cantidades_en_carrito(request):
    pedido_id = request.session.get("pedido_web")
    usuario_id = request.session.get("usuario_id")
    if not pedido_id or not usuario_id:
        return {}
    lineas = DetallePedidoModel.objects.filter(
        pedido_id=pedido_id, pedido__cliente_id=usuario_id, pedido__estado="BORRADOR",
    ).values_list("producto_id", "cantidad")
    return {str(producto_id): cantidad for producto_id, cantidad in lineas}
