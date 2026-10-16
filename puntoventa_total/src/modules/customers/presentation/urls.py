from django.urls import path
from src.modules.customers.presentation.views.historial_compras_view import historial_compras_view
from src.modules.customers.presentation.views.perfil_cliente_view import perfil_cliente_view
from src.modules.customers.presentation.views.registro_cliente_view import registro_cliente_view

app_name = "customers"

urlpatterns = [
    path("registro/", registro_cliente_view, name="registro"),
    path("perfil/<uuid:cliente_id>/", perfil_cliente_view, name="perfil"),
    path("historial/<uuid:cliente_id>/", historial_compras_view, name="historial"),
]

