from django import forms


class PedidoForm(forms.Form):
    modalidad = forms.ChoiceField(choices=[("RECOJO", "Recojo en tienda")])
    hora_recojo = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "1800"}))
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
        from django.utils import timezone
        hora = self.cleaned_data["hora_recojo"]
        if hora <= timezone.now() or hora.minute not in (0, 30) or hora.second or hora.microsecond:
            raise forms.ValidationError("Elige una franja futura de 30 minutos")
        return hora

