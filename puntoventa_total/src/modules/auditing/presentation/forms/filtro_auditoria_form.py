from django import forms


class FiltroAuditoriaForm(forms.Form):
    accion = forms.CharField(required=False, max_length=40)
    entidad = forms.CharField(required=False, max_length=60)
    entidad_id = forms.CharField(required=False, max_length=64)
    usuario_id = forms.UUIDField(required=False)
    desde = forms.DateField(required=False)
    hasta = forms.DateField(required=False)
    pagina = forms.IntegerField(required=False, min_value=1)

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta and hasta < desde:
            self.add_error("hasta", "La fecha fin no puede ser anterior a la de inicio")
        return datos
