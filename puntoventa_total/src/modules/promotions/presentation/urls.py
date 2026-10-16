from django.urls import path
from src.modules.promotions.presentation.views.promocion_view import promocion_editar_view, promocion_view
from src.modules.promotions.presentation.views.promociones_activas_view import promociones_activas_view

app_name = "promotions"

urlpatterns = [
    path("", promociones_activas_view, name="activas"),
    path("gestion/", promocion_view, name="promociones"),
    path("crear/", promocion_view, name="crear"),
    path("<uuid:promocion_id>/editar/", promocion_editar_view, name="editar"),
]
