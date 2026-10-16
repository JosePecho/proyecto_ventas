from django import forms


class FiltroReporteForm(forms.Form):
    RANGO_CHOICES = [
        ("hoy", "Hoy"),
        ("7", "Ultimos 7 dias"),
        ("30", "Ultimos 30 dias"),
        ("mes", "Mes actual"),
        ("personalizado", "Personalizado"),
    ]

    rango = forms.ChoiceField(choices=RANGO_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    desde = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    hasta = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    formato = forms.ChoiceField(
        required=False,
        choices=[("", "Ver en pantalla"), ("csv", "Exportar CSV"), ("pdf", "Exportar PDF")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def limpiar_a_rango(self):
        from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas

        if not self.is_valid():
            raise ValueError("Filtro invalido")
        datos = self.cleaned_data
        if datos["rango"] == "hoy":
            return RangoFechas.hoy()
        if datos["rango"] == "mes":
            return RangoFechas.del_mes()
        if datos["rango"] == "personalizado":
            if not datos["desde"] or not datos["hasta"]:
                raise ValueError("Indique fechas de inicio y fin")
            return RangoFechas(desde=datos["desde"], hasta=datos["hasta"])
        return RangoFechas.ultimos_dias(int(datos["rango"]))

