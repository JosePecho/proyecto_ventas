from django import forms


class RecepcionForm(forms.Form):
    producto_id = forms.UUIDField(widget=forms.HiddenInput())
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

