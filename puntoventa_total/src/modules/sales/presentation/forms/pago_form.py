from django import forms

from src.modules.sales.domain.value_objects.metodo_pago import MetodoPago


class PagoForm(forms.Form):
    metodo = forms.ChoiceField(
        choices=[(t, t) for t in MetodoPago.TIPOS],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    monto = forms.DecimalField(
        min_value=0.01, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "autofocus": True}),
    )
    monto_entregado = forms.DecimalField(
        required=False, min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    referencia = forms.CharField(
        max_length=80, required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def clean(self):
        datos = super().clean()
        if datos.get("metodo") == "EFECTIVO":
            entregado = datos.get("monto_entregado")
            monto = datos.get("monto")
            if entregado is not None and monto is not None and entregado < monto:
                self.add_error("monto_entregado", "El efectivo entregado no puede ser menor al monto")
        elif not datos.get("referencia"):
            self.add_error("referencia", "Indique la referencia del pago electronico")
        return datos

