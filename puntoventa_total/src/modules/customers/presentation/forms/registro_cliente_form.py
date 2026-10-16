from django import forms


class RegistroClienteForm(forms.Form):
    nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-control"}))
    dni = forms.CharField(
        max_length=8, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    telefono = forms.CharField(
        max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    direccion = forms.CharField(
        max_length=200, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def clean_dni(self):
        dni = self.cleaned_data.get("dni", "")
        if dni:
            from src.shared.domain.value_objects.dni import DNI

            return str(DNI(dni))
        return ""

