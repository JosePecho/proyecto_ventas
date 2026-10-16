from django.urls import path
from src.modules.orders.presentation.views.carrito_view import agregar_al_carrito, carrito_view
from src.modules.orders.presentation.views.checkout_view import checkout_view
from src.modules.orders.presentation.views.pedido_view import (
    detalle_pedido_view,
    mis_pedidos_view,
    pedidos_cocina_view,
)
from src.modules.orders.presentation.views.seguimiento_view import seguimiento_view

app_name = "orders"

urlpatterns = [
    path("carrito/", carrito_view, name="carrito"),
    path("carrito/agregar/<uuid:producto_id>/", agregar_al_carrito, name="agregar"),
    path("checkout/", checkout_view, name="checkout"),
    path("confirmacion/<uuid:pedido_id>/", detalle_pedido_view, name="confirmacion"),
    path("mis-pedidos/", mis_pedidos_view, name="mis_pedidos"),
    path("pedido/<uuid:pedido_id>/", detalle_pedido_view, name="detalle"),
    path("cocina/", pedidos_cocina_view, name="cocina"),
    path("seguimiento/", seguimiento_view, name="seguimiento"),
]
