from django import forms


class CierreForm(forms.Form):
    monto_fisico = forms.DecimalField(
        min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "autofocus": True}),
    )
    observaciones = forms.CharField(
        max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

