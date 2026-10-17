from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from src.modules.customers.application.dto.cliente_input import ActualizarClienteDTO
from src.modules.customers.application.use_cases.actualizar_cliente import ActualizarCliente
from src.modules.customers.application.use_cases.consultar_cliente import ConsultarCliente
from src.modules.customers.domain.exceptions.cliente_exceptions import ClienteException
from src.modules.customers.infrastructure.factories import construir_cliente_repository
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.customers.presentation.forms.perfil_cliente_form import PerfilClienteForm


@login_required
def perfil_cliente_view(request, cliente_id):
    cliente = get_object_or_404(ClienteModel, pk=cliente_id, activo=True)
    rol = request.session.get("rol")
    propietario = (
        cliente.usuario_id is not None
        and str(cliente.usuario_id) == request.session.get("usuario_id")
    )
    if rol not in {"ADMINISTRADOR", "GERENTE", "CAJERO"} and not (rol == "CLIENTE" and propietario):
        raise PermissionDenied("No tiene permisos para acceder a este perfil")

    if request.method == "POST":
        form = PerfilClienteForm(request.POST)
        if form.is_valid():
            try:
                ActualizarCliente(construir_cliente_repository()).ejecutar(
                    ActualizarClienteDTO(
                        cliente_id=cliente_id,
                        nombre=form.cleaned_data["nombre"],
                        email=form.cleaned_data.get("email", ""),
                        telefono=form.cleaned_data.get("telefono", ""),
                        direccion=form.cleaned_data.get("direccion", ""),
                    )
                )
            except ClienteException as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Perfil actualizado")
                return redirect("customers:perfil", cliente_id=cliente_id)
    else:
        form = PerfilClienteForm(
            initial={
                "nombre": cliente.nombre,
                "email": cliente.email,
                "telefono": cliente.telefono,
                "direccion": cliente.direccion,
            }
        )

    perfil = ConsultarCliente(construir_cliente_repository()).por_id(cliente_id)
    return render(request, "customers/perfil.html", {"form": form, "cliente": perfil})

