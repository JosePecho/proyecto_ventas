from django import forms


class AperturaForm(forms.Form):
    monto_apertura = forms.DecimalField(
        min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "autofocus": True}),
    )

