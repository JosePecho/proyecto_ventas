from django.urls import path
from src.modules.reporting.presentation.views.dashboard_view import dashboard_view
from src.modules.reporting.presentation.views.inventario_reporte_view import inventario_reporte_view
from src.modules.reporting.presentation.views.utilidad_reporte_view import utilidad_reporte_view
from src.modules.reporting.presentation.views.ventas_reporte_view import ventas_reporte_view
from src.modules.reporting.presentation.views.productos_reporte_view import productos_reporte_view

app_name = "reporting"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("ventas/", ventas_reporte_view, name="ventas"),
    path("productos/", productos_reporte_view, name="productos"),
    path("inventario/", inventario_reporte_view, name="inventario"),
    path("utilidad/", utilidad_reporte_view, name="utilidad"),
]
