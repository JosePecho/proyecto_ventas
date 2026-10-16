from django import forms

from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion


class PromocionForm(forms.Form):
    nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-control"}))
    tipo = forms.ChoiceField(choices=TipoPromocion.opciones(), widget=forms.Select(attrs={"class": "form-select"}))
    descuento_valor = forms.DecimalField(
        min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    producto_id = forms.UUIDField(required=False, widget=forms.HiddenInput())
    cantidad_requerida = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    cantidad_gratuita = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    vigencia_desde = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}))
    vigencia_hasta = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}))

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("vigencia_desde"), datos.get("vigencia_hasta")
        if desde and hasta and hasta <= desde:
            self.add_error("vigencia_hasta", "La fecha de fin debe ser posterior al inicio")
        if datos.get("tipo") == TipoPromocion.NX1.value and not datos.get("producto_id"):
            self.add_error("tipo", "NX1 requiere un producto especifico")
        return datos

