from django import forms


class VentaForm(forms.Form):
    cliente_id = forms.UUIDField(required=False, widget=forms.HiddenInput())
    observacion = forms.CharField(
        max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

