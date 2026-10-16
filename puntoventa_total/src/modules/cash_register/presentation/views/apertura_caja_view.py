from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from src.modules.cash_register.application.use_cases.abrir_turno import AbrirTurno
from src.modules.cash_register.domain.exceptions.caja_exceptions import CajaException
from src.modules.cash_register.infrastructure.factories import construir_turno_repository
from src.modules.cash_register.presentation.forms.apertura_form import AperturaForm
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE", "CAJERO")
def apertura_caja_view(request):
    if request.method == "POST":
        form = AperturaForm(request.POST)
        if form.is_valid():
            try:
                turno = AbrirTurno(construir_turno_repository()).ejecutar(
                    cajero_id=str(request.session.get("usuario_id", "")),
                    monto_apertura=form.cleaned_data["monto_apertura"],
                )
            except CajaException as exc:
                messages.error(request, str(exc))
            else:
                request.session["turno_caja_id"] = turno.id
                messages.success(request, "Caja abierta")
                return redirect("sales:pos")
    else:
        form = AperturaForm()

    return render(request, "cash_register/apertura.html", {"form": form})

