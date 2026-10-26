from django import forms
from datetime import timedelta
from django.utils import timezone


def proximo_horario_recojo():
    ahora = timezone.localtime()
    return ahora.replace(minute=0, second=0, microsecond=0) + timedelta(
        minutes=30 if ahora.minute < 30 else 60
    )


class PedidoForm(forms.Form):
    modalidad = forms.ChoiceField(choices=[("RECOJO", "Recojo en tienda")])
    hora_recojo = forms.DateTimeField(
        required=False,
        initial=proximo_horario_recojo,
        label="Fecha y hora estimada de recojo",
        help_text="Se asigna automáticamente el próximo horario de 30 minutos al confirmar tu pedido.",
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"class": "form-control", "type": "datetime-local", "disabled": True},
        ),
    )
    cliente_nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-control"}))
    cliente_telefono = forms.CharField(
        max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    cliente_dni = forms.CharField(
        max_length=8, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    observaciones = forms.CharField(
        max_length=255, required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2})
    )

    def clean_cliente_dni(self):
        dni = self.cleaned_data.get("cliente_dni", "")
        if dni:
            from src.shared.domain.value_objects.dni import DNI

            from src.shared.domain.exceptions.validation_exception import ValidationException
            try:
                return str(DNI(dni))
            except ValidationException as exc:
                raise forms.ValidationError(str(exc)) from exc
        return ""

    def clean_hora_recojo(self):
        hora = self.cleaned_data["hora_recojo"] or proximo_horario_recojo()
        if hora <= timezone.now() or hora.minute not in (0, 30) or hora.second or hora.microsecond:
            raise forms.ValidationError("Elige una franja futura de 30 minutos")
        return hora

