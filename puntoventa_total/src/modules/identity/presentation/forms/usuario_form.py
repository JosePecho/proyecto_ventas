from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm

from src.modules.identity.domain.enums.rol_usuario import RolUsuario


class UsuarioForm(ValidatedForm):
    username = forms.RegexField(r"^[\w.]{4,30}$", max_length=30, widget=forms.TextInput(attrs={"class": "form-control"}))
    nombre_completo = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    rol = forms.ChoiceField(choices=RolUsuario.opciones(), widget=forms.Select(attrs={"class": "form-select"}))

    def clean_password(self):
        from django.contrib.auth.password_validation import validate_password
        valor = self.cleaned_data.get("password")
        if valor:
            validate_password(valor)
        return valor

