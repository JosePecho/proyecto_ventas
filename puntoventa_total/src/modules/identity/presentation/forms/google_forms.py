from django import forms

from src.modules.customers.presentation.forms.registro_cliente_form import RegistroClienteForm
from src.modules.identity.presentation.forms.login_form import LoginForm


class CompletarGoogleForm(RegistroClienteForm):
    def __init__(self, *args, email=None, cliente_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].initial = email
        self.fields["email"].disabled = email is not None
        self.fields["email"].required = True
        self.fields["dni"].required = True
        self.fields["telefono"].required = True
        self.cliente_id = cliente_id

    def clean_dni(self):
        from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel

        dni = super().clean_dni()
        coincidencias = ClienteModel.objects.filter(dni=dni)
        if self.cliente_id:
            coincidencias = coincidencias.exclude(pk=self.cliente_id)
        if coincidencias.exists():
            raise forms.ValidationError("El DNI ya está registrado. Contacta al administrador para revisar tu cuenta.")
        return dni


class VincularGoogleForm(LoginForm):
    confirmar = forms.BooleanField(label="Autorizo vincular esta cuenta Google a mi usuario existente.",
                                   widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
