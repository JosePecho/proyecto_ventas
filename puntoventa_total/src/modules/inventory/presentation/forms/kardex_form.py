from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class KardexForm(ValidatedForm):
    producto_id = forms.ModelChoiceField(
        queryset=None, required=False, label="Producto",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    pagina = forms.IntegerField(min_value=1, required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
        self.fields["producto_id"].queryset = ProductoModel.objects.all()

    def clean(self):
        datos = super().clean()
        if datos.get("desde") and datos.get("hasta") and datos["desde"] > datos["hasta"]:
            self.add_error("hasta", "La fecha final debe ser posterior a la inicial")
        return datos
