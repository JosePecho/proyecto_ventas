from django.urls import path
from src.modules.catalog.presentation.views.categoria_view import categoria_view
from src.modules.catalog.presentation.views.catalogo_view import catalogo_view
from src.modules.catalog.presentation.views.producto_admin_view import (
    producto_descontinuar_view,
    producto_form_view,
    productos_admin,
)
from src.modules.catalog.presentation.views.producto_detalle_view import producto_detalle_view

app_name = "catalog"

urlpatterns = [
    path("", catalogo_view, name="catalogo"),
    path("productos/admin/", productos_admin, name="productos_admin"),
    path("productos/nuevo/", producto_form_view, name="producto_nuevo"),
    path("productos/<uuid:producto_id>/editar/", producto_form_view, name="producto_editar"),
    path("productos/<uuid:producto_id>/descontinuar/", producto_descontinuar_view, name="producto_descontinuar"),
    path("productos/<uuid:producto_id>/", producto_detalle_view, name="producto_detalle"),
    path("categorias/", categoria_view, name="categorias"),
]
