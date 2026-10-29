from django import forms

from src.shared.infrastructure.form_validation import ValidatedForm


class LoginForm(ValidatedForm):
    username = forms.CharField(
        label="Usuario o email",
        max_length=254,
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

