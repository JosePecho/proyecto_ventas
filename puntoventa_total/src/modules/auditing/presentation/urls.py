from django.urls import path
from src.modules.auditing.presentation.views.auditoria_view import auditoria_view

app_name = "auditing"

urlpatterns = [
    path("", auditoria_view, name="registros"),
]
