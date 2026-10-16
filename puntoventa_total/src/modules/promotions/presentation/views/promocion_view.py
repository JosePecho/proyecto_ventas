from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from src.modules.promotions.application.dto.promocion_input import PromocionInputDTO
from src.modules.promotions.application.use_cases.activar_promocion import ActivarPromocion
from src.modules.promotions.application.use_cases.cancelar_promocion import CancelarPromocion
from src.modules.promotions.application.use_cases.crear_promocion import CrearPromocion
from src.modules.promotions.domain.exceptions.promocion_exceptions import PromocionException
from src.modules.promotions.infrastructure.factories import construir_promocion_repository
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.promotions.presentation.forms.promocion_form import PromocionForm
from src.modules.identity.presentation.permissions.role_required import role_required


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def promocion_view(request):
    repo = construir_promocion_repository()

    if request.method == "POST":
        accion = request.POST.get("accion", "crear")
        promocion_id = request.POST.get("promocion_id")
        try:
            if accion == "crear":
                form = PromocionForm(request.POST)
                if form.is_valid():
                    CrearPromocion(repo).ejecutar(
                        PromocionInputDTO(
                            nombre=form.cleaned_data["nombre"],
                            tipo=form.cleaned_data["tipo"],
                            descuento_valor=form.cleaned_data["descuento_valor"],
                            producto_id=form.cleaned_data.get("producto_id"),
                            cantidad_requerida=form.cleaned_data.get("cantidad_requerida", 0),
                            cantidad_gratuita=form.cleaned_data.get("cantidad_gratuita", 0),
                            vigencia_desde=form.cleaned_data.get("vigencia_desde"),
                            vigencia_hasta=form.cleaned_data.get("vigencia_hasta"),
                        )
                    )
                    messages.success(request, "Promocion creada")
            elif accion == "activar":
                ActivarPromocion(repo).ejecutar(promocion_id)
                messages.success(request, "Promocion activada")
            elif accion == "cancelar":
                CancelarPromocion(repo).ejecutar(promocion_id, request.POST.get("motivo", ""))
                messages.info(request, "Promocion cancelada")
        except PromocionException as exc:
            messages.error(request, str(exc))
        return redirect("promotions:promociones")

    form = PromocionForm()
    return render(request, "promotions/index.html", {"form": form, "promociones": repo.listar(incluir_finalizadas=True)})


@login_required
@role_required("ADMINISTRADOR", "GERENTE")
def promocion_editar_view(request, promocion_id):
    promocion = get_object_or_404(PromocionModel, pk=promocion_id)
    if request.method == "POST":
        form = PromocionForm(request.POST)
        if form.is_valid():
            from src.modules.promotions.application.use_cases.actualizar_promocion import ActualizarPromocion

            try:
                ActualizarPromocion(construir_promocion_repository()).ejecutar(
                    promocion_id, form.cleaned_data["nombre"], form.cleaned_data["descuento_valor"]
                )
                messages.success(request, "Promocion actualizada")
            except PromocionException as exc:
                messages.error(request, str(exc))
            return redirect("promotions:promociones")
    return render(request, "promotions/editar.html", {"promocion": promocion})

