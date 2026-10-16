from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

