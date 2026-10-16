"""Decorador de vista: exige rol minimo para ejecutar la vista."""
from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from src.modules.identity.domain.services.politica_permisos import PoliticaPermisos


def role_required(*roles_permitidos):
    """Bloquea la vista si el usuario autenticado no tiene uno de los roles.

    Se apoya en el permiso `request.session["rol"]` que fija el login.
    """

    def envolver(vista):
        @wraps(vista)
        def interna(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("identity:login")
            rol = request.session.get("rol", "")
            if roles_permitidos and rol not in roles_permitidos:
                messages.error(request, "No tiene permisos para acceder a esta seccion")
                return redirect("catalog:catalogo")
            return vista(request, *args, **kwargs)

        return interna

    return envolver


def permission_required(permiso: str):
    """Variante fina basada en la politica de permisos del dominio."""

    def envolver(vista):
        @wraps(vista)
        def interna(request, *args, **kwargs):
            from src.modules.identity.domain.enums.rol_usuario import RolUsuario

            rol = RolUsuario(request.session.get("rol", RolUsuario.CLIENTE.value))
            if not PoliticaPermisos.puede(rol, permiso):
                messages.error(request, "Permiso denegado")
                return redirect("catalog:catalogo")
            return vista(request, *args, **kwargs)

        return interna

    return envolver

