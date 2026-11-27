from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class VentaForm(ValidatedForm):
    cliente_id = forms.UUIDField(required=False, widget=forms.HiddenInput())
    observacion = forms.CharField(
        max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

