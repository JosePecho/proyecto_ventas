from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from src.modules.identity.presentation.permissions.role_required import role_required
from src.modules.promotions.application.dto.promocion_input import PromocionInputDTO
from src.modules.promotions.application.use_cases.crear_promocion import CrearPromocion
from src.modules.promotions.domain.enums.estado_promocion import EstadoPromocion
from src.modules.promotions.infrastructure.factories import construir_promocion_repository
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.promotions.presentation.forms.promocion_form import PromocionForm
from src.shared.domain.exceptions.domain_exception import DomainException


def datos_form(form):
    datos = dict(form.cleaned_data)
    datos["producto_id"] = str(datos["producto_id"]) if datos.get("producto_id") else None
    return PromocionInputDTO(**datos)


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def promocion_view(request):
    repo = construir_promocion_repository()
    form = PromocionForm(request.POST or None)
    if request.method == "POST":
        accion = request.POST.get("accion", "crear")
        try:
            with transaction.atomic():
                if accion == "crear":
                    if form.is_valid():
                        CrearPromocion(repo).ejecutar(datos_form(form))
                        return redirect("promotions:promociones")
                elif accion in ("activar", "cancelar"):
                    from django import forms
                    try:
                        promocion_id = forms.UUIDField().clean(request.POST.get("promocion_id"))
                    except forms.ValidationError:
                        form.add_error(None, "Identificador de promoción inválido")
                    else:
                        get_object_or_404(PromocionModel.objects.select_for_update(), pk=promocion_id)
                        promo = repo.buscar_por_id(promocion_id)
                        promo.activar() if accion == "activar" else promo.cancelar()
                        repo.guardar(promo)
                        return redirect("promotions:promociones")
                else:
                    form.add_error(None, "Acción no válida")
        except DomainException as exc:
            form.add_error(None, str(exc))
    return render(request, "promotions/index.html", {"form": form, "promociones": repo.listar(incluir_finalizadas=True)})


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def promocion_editar_view(request, promocion_id):
    modelo = get_object_or_404(PromocionModel, pk=promocion_id)
    inicial = {campo: getattr(modelo, campo) for campo in PromocionForm.base_fields}
    form = PromocionForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                modelo = get_object_or_404(PromocionModel.objects.select_for_update(), pk=promocion_id)
                if modelo.estado in ("FINALIZADA", "CANCELADA"):
                    raise DomainException("No se puede editar una promoción terminada")
                repo = construir_promocion_repository()
                nuevo = CrearPromocion(repo).crear_entidad(datos_form(form))
                nuevo.id = modelo.id
                if modelo.estado == "ACTIVA":
                    nuevo.estado = EstadoPromocion.ACTIVA
                repo.guardar(nuevo)
            messages.success(request, "Promoción actualizada")
            return redirect("promotions:promociones")
        except DomainException as exc:
            form.add_error(None, str(exc))
    return render(request, "promotions/editar.html", {"promocion": modelo, "form": form})
