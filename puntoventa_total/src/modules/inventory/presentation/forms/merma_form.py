from django import forms

from src.modules.inventory.domain.enums.motivo_merma import MotivoMerma


class MermaForm(forms.Form):
    producto_id = forms.ModelChoiceField(queryset=None, label="Producto", widget=forms.Select(attrs={"class": "form-select"}))
    lote_id = forms.ModelChoiceField(queryset=None, required=False, label="Lote (opcional)", widget=forms.Select(attrs={"class": "form-select"}))
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    motivo = forms.ChoiceField(choices=MotivoMerma.opciones(), widget=forms.Select(attrs={"class": "form-select"}))
    observacion = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
        from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
        self.fields["producto_id"].queryset = ProductoModel.objects.filter(activo=True, requiere_stock=True)
        self.fields["lote_id"].queryset = LoteModel.objects.filter(activo=True, cantidad_restante__gt=0)

    def clean(self):
        datos = super().clean()
        producto, lote = datos.get("producto_id"), datos.get("lote_id")
        if producto and lote and producto.pk != lote.producto_id:
            self.add_error("lote_id", "El lote no pertenece al producto seleccionado")
        return datos
