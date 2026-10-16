from django import forms

from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento


class AjusteStockForm(forms.Form):
    producto_id = forms.UUIDField(widget=forms.HiddenInput())
    tipo = forms.ChoiceField(
        choices=[
            (TipoMovimiento.AJUSTE_POSITIVO.value, "Ajuste positivo (sobrante)"),
            (TipoMovimiento.AJUSTE_NEGATIVO.value, "Ajuste negativo (faltante)"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    observacion = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))

    def a_diferencia(self) -> int:
        cantidad = self.cleaned_data["cantidad"]
        return cantidad if self.cleaned_data["tipo"] == TipoMovimiento.AJUSTE_POSITIVO.value else -cantidad

