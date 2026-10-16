"""Permisos especificos del modulo de ventas."""
from django.contrib.auth.decorators import login_required

from src.modules.identity.presentation.permissions.role_required import role_required

requiere_cajero = role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
requiere_gerente_anulacion = role_required("ADMINISTRADOR", "GERENTE")


def requiere_caja_abierta(vista):
    """Exige turno de caja abierto para cobrar."""

    def interna(request, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect

        if not request.session.get("turno_caja_id"):
            messages.error(request, "Debe abrir caja para operar el POS")
            return redirect("cash_register:apertura")
        return vista(request, *args, **kwargs)

    return interna

