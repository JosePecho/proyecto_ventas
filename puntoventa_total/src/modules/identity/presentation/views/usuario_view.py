"""CRUD de usuarios para administradores."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from src.modules.identity.application.dto.usuario_input import ActualizarUsuarioDTO, UsuarioInputDTO
from src.modules.identity.application.use_cases.actualizar_usuario import ActualizarUsuario
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.application.use_cases.desactivar_usuario import DesactivarUsuario
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.identity.presentation.forms.usuario_form import UsuarioForm
from src.modules.identity.presentation.permissions.role_required import role_required
from django.shortcuts import get_object_or_404
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
from src.shared.domain.exceptions.domain_exception import DomainException
from django.db import transaction


@login_required
@role_required("ADMINISTRADOR")
def lista_usuarios(request):
    repo = construir_repositorio()
    usuarios = repo.listar(incluir_inactivos=True)
    return render(request, "identity/usuarios.html", {"usuarios": usuarios})


@login_required
@role_required("ADMINISTRADOR")
def crear_usuario_view(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            try:
                CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
                    UsuarioInputDTO(
                        username=form.cleaned_data["username"],
                        password=form.cleaned_data["password"],
                        nombre_completo=form.cleaned_data["nombre_completo"],
                        email=form.cleaned_data.get("email", ""),
                        rol=form.cleaned_data["rol"],
                    )
                )
            except DomainException as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Usuario creado correctamente")
                return redirect("identity:usuarios")
    else:
        form = UsuarioForm()
    return render(request, "identity/usuarios.html", {"form": form})


@login_required
@role_required("ADMINISTRADOR")
def desactivar_usuario_view(request, usuario_id):
    if request.method == "POST":
        try:
            with transaction.atomic():
                list(UsuarioModel.objects.select_for_update().filter(rol="ADMINISTRADOR", activo=True).order_by("id"))
                DesactivarUsuario(construir_repositorio()).ejecutar(usuario_id)
            messages.success(request, "Usuario desactivado")
        except DomainException as exc:
            messages.error(request, str(exc))
    return redirect("identity:usuarios")


@login_required
@role_required("ADMINISTRADOR")
def editar_usuario_view(request, usuario_id):
    modelo = get_object_or_404(UsuarioModel, pk=usuario_id)
    form = UsuarioForm(request.POST or None, initial={"username": modelo.username,
        "nombre_completo": modelo.nombre_completo, "email": modelo.email, "rol": modelo.rol})
    form.fields["username"].disabled = True
    form.fields["password"].required = False
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                administradores = list(UsuarioModel.objects.select_for_update().filter(rol="ADMINISTRADOR", activo=True).order_by("id"))
                if modelo.rol == "ADMINISTRADOR" and form.cleaned_data["rol"] != "ADMINISTRADOR" and len(administradores) <= 1:
                    raise DomainException("No se puede quitar el rol al último administrador")
                ActualizarUsuario(construir_repositorio(), construir_hasher()).ejecutar(ActualizarUsuarioDTO(
                    usuario_id=str(usuario_id), nombre_completo=form.cleaned_data["nombre_completo"],
                    email=form.cleaned_data["email"], rol=form.cleaned_data["rol"],
                    password_nueva=form.cleaned_data.get("password") or None))
        except DomainException as exc:
            form.add_error(None, str(exc))
        else:
            return redirect("identity:usuarios")
    return render(request, "identity/usuario_editar.html", {"form": form})

