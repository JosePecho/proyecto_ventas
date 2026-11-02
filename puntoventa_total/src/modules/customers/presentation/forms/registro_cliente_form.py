from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class RegistroClienteForm(ValidatedForm):
    nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-control"}))
    dni = forms.RegexField(
        r"^[0-9]{8}$", max_length=8, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    telefono = forms.CharField(
        max_length=9, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    direccion = forms.CharField(
        max_length=200, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def clean_dni(self):
        dni = self.cleaned_data.get("dni", "")
        if dni:
            from src.shared.domain.exceptions.validation_exception import ValidationException
            from src.shared.domain.value_objects.dni import DNI
            try:
                return str(DNI(dni))
            except ValidationException as exc:
                raise forms.ValidationError(str(exc)) from exc
        return dni

