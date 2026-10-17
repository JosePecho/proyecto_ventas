from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .registro_cliente_form import RegistroClienteForm


class RegistroWebForm(RegistroClienteForm):
    telefono = forms.RegexField(r"^\+?[0-9]{7,15}$", max_length=16,
                                error_messages={"invalid": "Ingresa un teléfono de 7 a 15 dígitos"})
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password_confirmacion = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ("dni", "email", "telefono"):
            self.fields[campo].required = True

    def clean_email(self):
        from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
        email = self.cleaned_data["email"].strip().lower()
        if UsuarioModel.objects.filter(email__iexact=email).exists():
            raise ValidationError("El email ya tiene una cuenta")
        return email

    def clean_dni(self):
        from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
        dni = super().clean_dni()
        if ClienteModel.objects.filter(dni=dni).exists():
            raise ValidationError("El DNI ya está registrado")
        return dni

    def clean(self):
        datos = super().clean()
        password = datos.get("password")
        if password:
            validate_password(password)
        if password != datos.get("password_confirmacion"):
            self.add_error("password_confirmacion", "Las contraseñas no coinciden")
        return datos
