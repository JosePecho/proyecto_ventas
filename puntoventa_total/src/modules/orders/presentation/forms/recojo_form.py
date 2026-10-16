from django import forms


class RecojoForm(forms.Form):
    hora_recojo = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        help_text="Franjas cada 30 minutos dentro del horario de atencion",
    )

