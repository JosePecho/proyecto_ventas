from django.urls import path
from src.modules.sales.presentation.views.anulacion_view import anulacion_view
from src.modules.sales.presentation.views.pago_view import pago_view
from src.modules.sales.presentation.views.pos_view import (
    agregar_producto_pos,
    buscar_producto_pos,
    eliminar_producto_pos,
    modificar_cantidad_pos,
    pos_view,
)
from src.modules.sales.presentation.views.ticket_view import ticket_view
from src.modules.sales.presentation.views.venta_view import ventas_dia_view

app_name = "sales"

urlpatterns = [
    path("", pos_view, name="pos"),
    path("buscar/", buscar_producto_pos, name="buscar"),
    path("ventas/", ventas_dia_view, name="ventas"),
    path("venta/<uuid:venta_id>/agregar/<uuid:producto_id>/", agregar_producto_pos, name="agregar"),
    path("venta/<uuid:venta_id>/cantidad/<uuid:producto_id>/", modificar_cantidad_pos, name="modificar_cantidad"),
    path("venta/<uuid:venta_id>/eliminar/<uuid:producto_id>/", eliminar_producto_pos, name="eliminar"),
    path("venta/<uuid:venta_id>/pago/", pago_view, name="pago"),
    path("venta/<uuid:venta_id>/ticket/", ticket_view, name="ticket"),
    path("venta/<uuid:venta_id>/anular/", anulacion_view, name="anular"),
]
