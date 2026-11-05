from django.urls import path

from src.modules.identity.presentation.views.google_login_view import google_login_view
from src.modules.identity.presentation.views.login_view import login_view
from src.modules.identity.presentation.views.logout_view import logout_view
from src.modules.identity.presentation.views.usuario_view import (
    crear_usuario_view,
    desactivar_usuario_view,
    editar_usuario_view,
    lista_usuarios,
)

app_name = "identity"

urlpatterns = [
    path("", login_view, name="login"),
    path("login/", login_view, name="login"),
    path("login/google/", google_login_view, name="google_login"),
    path("logout/", logout_view, name="logout"),
    path("usuarios/", lista_usuarios, name="usuarios"),
    path("usuarios/nuevo/", crear_usuario_view, name="usuario_nuevo"),
    path("usuarios/<uuid:usuario_id>/editar/", editar_usuario_view, name="usuario_editar"),
    path("usuarios/<uuid:usuario_id>/desactivar/", desactivar_usuario_view, name="usuario_desactivar"),
]
