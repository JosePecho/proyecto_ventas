from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class RecepcionForm(ValidatedForm):
    producto_id = forms.ModelChoiceField(queryset=None, label="Producto", widget=forms.Select(attrs={"class": "form-select"}))
    numero_lote = forms.CharField(max_length=40, widget=forms.TextInput(attrs={"class": "form-control"}))
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    costo_unitario = forms.DecimalField(
        min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    proveedor = forms.CharField(max_length=120, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    fecha_vencimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
        self.fields["producto_id"].queryset = ProductoModel.objects.filter(activo=True, requiere_stock=True)

    def clean_producto_id(self):
        return str(self.cleaned_data["producto_id"].pk)

