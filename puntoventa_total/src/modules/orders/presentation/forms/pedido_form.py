from django import forms


class PedidoForm(forms.Form):
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

            return str(DNI(dni))
        return ""

