from django import forms

from src.modules.identity.domain.enums.rol_usuario import RolUsuario


class UsuarioForm(forms.Form):
    username = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"class": "form-control"}))
    nombre_completo = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    rol = forms.ChoiceField(choices=RolUsuario.opciones(), widget=forms.Select(attrs={"class": "form-select"}))

