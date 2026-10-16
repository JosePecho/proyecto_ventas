from django.urls import path
from src.modules.cash_register.presentation.views.apertura_caja_view import apertura_caja_view
from src.modules.cash_register.presentation.views.arqueo_view import arqueo_view
from src.modules.cash_register.presentation.views.cierre_caja_view import cierre_caja_view

app_name = "cash_register"

urlpatterns = [
    path("apertura/", apertura_caja_view, name="apertura"),
    path("cierre/", cierre_caja_view, name="cierre"),
    path("arqueo/", arqueo_view, name="arqueo"),
]

