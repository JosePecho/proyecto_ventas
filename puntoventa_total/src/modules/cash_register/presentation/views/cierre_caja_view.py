from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from src.modules.cash_register.application.use_cases.consultar_arqueo import ConsultarArqueo
from src.modules.cash_register.application.use_cases.cerrar_turno import CerrarTurno
from src.modules.cash_register.domain.exceptions.caja_exceptions import CajaException
from src.modules.cash_register.infrastructure.factories import construir_turno_repository
from src.modules.cash_register.infrastructure.factories import construir_ventas_turno_port
from src.modules.cash_register.presentation.forms.cierre_form import CierreForm
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
def cierre_caja_view(request):
    turno_id = request.session.get("turno_caja_id")
    if not turno_id:
        messages.error(request, "No hay turno abierto")
        return redirect("cash_register:apertura")

    arqueo = ConsultarArqueo(construir_turno_repository(), construir_ventas_turno_port()).ejecutar(turno_id)

    if request.method == "POST":
        form = CierreForm(request.POST)
        if form.is_valid():
            try:
                resultado = CerrarTurno(
                    construir_turno_repository(), construir_ventas_turno_port(), uow=transaction.atomic()
                ).ejecutar(
                    turno_id=turno_id,
                    monto_fisico=form.cleaned_data["monto_fisico"],
                    usuario_id=str(request.session.get("usuario_id", "")),
                    observaciones=form.cleaned_data.get("observaciones", ""),
                )
            except CajaException as exc:
                messages.error(request, str(exc))
            else:
                request.session.pop("turno_caja_id", None)
                mensajes = "Cierre exacto" if resultado.congruente else f"Diferencia: {resultado.diferencia:.2f}"
                messages.success(request, f"Turno cerrado. {mensajes}")
                return redirect("cash_register:arqueo")
    else:
        form = CierreForm(initial={"monto_fisico": arqueo.saldo_sistema})

    return render(request, "cash_register/cierre.html", {"form": form, "arqueo": arqueo})

