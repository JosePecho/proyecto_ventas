from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class PerfilClienteForm(ValidatedForm):
    nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    telefono = forms.CharField(
        max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    direccion = forms.CharField(
        max_length=200, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

