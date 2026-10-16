"""CRUD de usuarios para administradores."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from src.modules.identity.application.dto.usuario_input import ActualizarUsuarioDTO, UsuarioInputDTO
from src.modules.identity.application.use_cases.actualizar_usuario import ActualizarUsuario
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.application.use_cases.desactivar_usuario import DesactivarUsuario
from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioException
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.identity.presentation.forms.usuario_form import UsuarioForm
from src.modules.identity.presentation.permissions.role_required import role_required


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
            except UsuarioException as exc:
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
            DesactivarUsuario(construir_repositorio()).ejecutar(usuario_id)
            messages.success(request, "Usuario desactivado")
        except UsuarioException as exc:
            messages.error(request, str(exc))
    return redirect("identity:usuarios")

