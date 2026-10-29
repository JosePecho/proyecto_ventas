from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class CategoriaForm(ValidatedForm):
    nombre = forms.CharField(max_length=80, widget=forms.TextInput(attrs={"class": "form-control"}))
    descripcion = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2})
    )

