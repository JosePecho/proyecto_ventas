from django.urls import path
from src.modules.inventory.presentation.views.alertas_view import alertas_view
from src.modules.inventory.presentation.views.inventario_view import inventario_view
from src.modules.inventory.presentation.views.kardex_view import kardex_view
from src.modules.inventory.presentation.views.merma_view import merma_view
from src.modules.inventory.presentation.views.recepcion_view import recepcion_view

app_name = "inventory"

urlpatterns = [
    path("", inventario_view, name="inventario"),
    path("recepcion/", recepcion_view, name="recepcion"),
    path("mermas/", merma_view, name="mermas"),
    path("kardex/", kardex_view, name="kardex"),
    path("alertas/", alertas_view, name="alertas"),
]
