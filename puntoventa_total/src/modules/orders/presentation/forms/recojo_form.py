from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class RecojoForm(ValidatedForm):
    hora_recojo = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        help_text="Franjas cada 30 minutos dentro del horario de atencion",
    )

