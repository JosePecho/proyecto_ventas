from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class AperturaForm(ValidatedForm):
    monto_apertura = forms.DecimalField(
        min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "autofocus": True}),
    )

