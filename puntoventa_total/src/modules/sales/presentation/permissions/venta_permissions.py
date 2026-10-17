"""Permisos especificos del modulo de ventas."""
from functools import wraps

from django.shortcuts import get_object_or_404

from src.modules.identity.presentation.permissions.role_required import role_required

requiere_cajero = role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
requiere_gerente_anulacion = role_required("ADMINISTRADOR", "GERENTE")


def venta_propia(vista):
    """Una sesion de caja solo puede modificar sus propias ventas."""
    @wraps(vista)
    def interna(request, venta_id, *args, **kwargs):
        from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
        get_object_or_404(VentaModel, pk=venta_id, cajero_id=request.session.get("usuario_id"))
        return vista(request, venta_id, *args, **kwargs)
    return interna


def requiere_caja_abierta(vista):
    """Exige turno de caja abierto para cobrar."""

    @wraps(vista)
    def interna(request, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect

        from src.modules.cash_register.infrastructure.persistence.django_models.turno_caja_model import TurnoCajaModel
        turno = TurnoCajaModel.objects.filter(
            cajero_id=request.session.get("usuario_id"), estado="ABIERTO"
        ).first()
        if turno is None:
            request.session.pop("turno_caja_id", None)
            messages.error(request, "Debe abrir caja para operar el POS")
            return redirect("cash_register:apertura")
        request.session["turno_caja_id"] = str(turno.pk)
        return vista(request, *args, **kwargs)

    return interna

