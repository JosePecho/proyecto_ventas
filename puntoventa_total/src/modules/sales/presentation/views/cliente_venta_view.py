from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.db import transaction

from src.modules.sales.presentation.permissions.venta_permissions import requiere_cajero
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.infrastructure.factories import construir_venta_repository, construir_promociones_port
from src.modules.sales.application.use_cases.preparar_beneficios import PrepararBeneficiosVenta


@login_required
@requiere_cajero
def asignar_cliente_view(request, venta_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    cliente = get_object_or_404(ClienteModel, dni=request.POST.get("dni", ""), activo=True)
    with transaction.atomic():
        modelo = get_object_or_404(VentaModel.objects.select_for_update(), pk=venta_id,
                                   cajero_id=request.session.get("usuario_id"), estado="BORRADOR")
        if modelo.pagos.exists():
            return HttpResponseBadRequest("No se cambia cliente después de iniciar el pago")
        modelo.cliente_id = cliente.id
        modelo.save(update_fields=["cliente_id"])
        PrepararBeneficiosVenta(construir_venta_repository(), construir_promociones_port()).ejecutar(venta_id)
    return redirect("sales:pago", venta_id=venta_id)
