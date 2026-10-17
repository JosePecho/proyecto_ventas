from datetime import timedelta

from django import forms
from django.utils import timezone

from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas
from src.shared.domain.exceptions.validation_exception import ValidationException


class RangoReporteForm(forms.Form):
    desde = forms.DateField()
    hasta = forms.DateField()

    def clean(self):
        datos = super().clean()
        if datos.get("desde") and datos.get("hasta"):
            try:
                RangoFechas(datos["desde"], datos["hasta"])
            except ValidationException as exc:
                raise forms.ValidationError(str(exc)) from exc
        return datos

    @classmethod
    def de_request(cls, request):
        hoy = timezone.localdate()
        return cls({"desde": request.GET.get("desde", (hoy - timedelta(days=30)).isoformat()),
                    "hasta": request.GET.get("hasta", hoy.isoformat())})
