from django import forms


class CategoriaForm(forms.Form):
    nombre = forms.CharField(max_length=80, widget=forms.TextInput(attrs={"class": "form-control"}))
    descripcion = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2})
    )

