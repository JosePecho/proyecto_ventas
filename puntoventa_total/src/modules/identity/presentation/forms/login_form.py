from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuario o email",
        max_length=254,
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

