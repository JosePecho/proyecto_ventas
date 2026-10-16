from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from src.modules.customers.application.dto.cliente_input import ClienteInputDTO
from src.modules.customers.application.use_cases.registrar_cliente import RegistrarCliente
from src.modules.customers.domain.exceptions.cliente_exceptions import ClienteException
from src.modules.customers.infrastructure.factories import construir_cliente_repository
from src.modules.customers.presentation.forms.registro_cliente_form import RegistroClienteForm


@login_required
def registro_cliente_view(request):
    if request.method == "POST":
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            try:
                cliente = RegistrarCliente(construir_cliente_repository()).ejecutar(
                    ClienteInputDTO(
                        nombre=form.cleaned_data["nombre"],
                        dni=form.cleaned_data.get("dni") or None,
                        email=form.cleaned_data.get("email", ""),
                        telefono=form.cleaned_data.get("telefono", ""),
                        direccion=form.cleaned_data.get("direccion", ""),
                        usuario_id=str(request.session.get("usuario_id", "")) or None,
                    )
                )
            except ClienteException as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, f"Cliente {cliente.nombre} registrado")
                return redirect("customers:perfil", cliente_id=cliente.id)
    else:
        form = RegistroClienteForm()
    return render(request, "customers/registro.html", {"form": form})

