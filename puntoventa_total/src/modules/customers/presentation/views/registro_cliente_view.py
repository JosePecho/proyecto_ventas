from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render

from src.modules.customers.application.dto.cliente_input import ClienteInputDTO
from src.modules.customers.application.use_cases.registrar_cliente import RegistrarCliente
from src.shared.domain.exceptions.domain_exception import DomainException
from src.modules.customers.infrastructure.factories import construir_cliente_repository
from src.modules.customers.presentation.forms.registro_cliente_form import RegistroClienteForm


def registro_cliente_view(request):
    if not request.user.is_authenticated:
        return registro_web_view(request)
    if request.session.get("rol") not in ("ADMINISTRADOR", "GERENTE", "CAJERO"):
        return redirect("catalog:catalogo")
    if request.method == "POST":
        form = RegistroClienteForm(request.POST)
        for campo in ("dni", "telefono"):
            form.fields[campo].required = True
        if form.is_valid():
            try:
                cliente = RegistrarCliente(construir_cliente_repository()).ejecutar(
                    ClienteInputDTO(
                        nombre=form.cleaned_data["nombre"],
                        dni=form.cleaned_data.get("dni") or None,
                        email=form.cleaned_data.get("email", ""),
                        telefono=form.cleaned_data.get("telefono", ""),
                        direccion=form.cleaned_data.get("direccion", ""),
                        usuario_id=None,
                    )
                )
            except DomainException as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, f"Cliente {cliente.nombre} registrado")
                return redirect("customers:perfil", cliente_id=cliente.id)
    else:
        form = RegistroClienteForm()
        for campo in ("dni", "telefono"):
            form.fields[campo].required = True
    return render(request, "customers/registro.html", {"form": form})


def registro_web_view(request):
    from hashlib import sha256
    from django.db import IntegrityError, transaction
    from src.modules.customers.presentation.forms.registro_web_form import RegistroWebForm
    from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
    from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
    from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
    from src.shared.domain.exceptions.domain_exception import DomainException

    form = RegistroWebForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            with transaction.atomic():
                usuario = CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
                    UsuarioInputDTO(
                        username="web." + sha256(datos["email"].encode()).hexdigest()[:26],
                        password=datos["password"], nombre_completo=datos["nombre"],
                        email=datos["email"], rol="CLIENTE",
                    )
                )
                RegistrarCliente(construir_cliente_repository()).ejecutar(
                    ClienteInputDTO(nombre=datos["nombre"], dni=datos["dni"],
                                    email=datos["email"], telefono=datos["telefono"],
                                    usuario_id=usuario.id)
                )
        except (DomainException, IntegrityError):
            form.add_error(None, "No se pudo registrar: DNI o email ya registrado")
        else:
            messages.success(request, "Cuenta creada. Inicia sesión con tu email y contraseña.")
            return redirect("identity:login")
    return render(request, "customers/registro.html", {"form": form})

