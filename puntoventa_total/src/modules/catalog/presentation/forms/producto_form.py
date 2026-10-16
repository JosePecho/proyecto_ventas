from django import forms


class ProductoForm(forms.Form):
    nombre = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    descripcion = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )
    codigo_barras = forms.CharField(
        max_length=14,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "EAN-13 o interno"}),
    )
    costo = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    precio_venta = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    categoria_id = forms.UUIDField(required=False, widget=forms.HiddenInput())
    imagen = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"}))

    def clean(self):
        datos = super().clean()
        costo, venta = datos.get("costo"), datos.get("precio_venta")
        if costo is not None and venta is not None and venta <= costo:
            self.add_error("precio_venta", "El precio de venta debe superar el costo")
        return datos

