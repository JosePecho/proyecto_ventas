"""Reglas de formato compartidas por los formularios HTML y el servidor."""
from django import forms
from django.core.validators import RegexValidator


FORMATOS = {
    "dni": (r"[0-9]{8}", "Ingresa exactamente 8 dígitos.", 8, "numeric"),
    "telefono": (r"\+?[0-9]{7,15}", "Ingresa de 7 a 15 dígitos, con + opcional al inicio.", 16, "tel"),
    "codigo_barras": (r"(?:[0-9]{8}|[0-9]{12,14})", "Ingresa 8, 12, 13 o 14 dígitos.", 14, "numeric"),
}


class ValidatedForm(forms.Form):
    """Conserva los tipos Django y añade formatos a los campos correspondientes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if isinstance(campo.widget, forms.PasswordInput):
                # Las contraseñas deben conservar exactamente lo escrito.
                campo.strip = False
                continue
            clave = nombre.removeprefix("cliente_")
            if clave in FORMATOS:
                patron, mensaje, longitud, modo = FORMATOS[clave]
                campo.validators.append(RegexValidator(r"\A(?:" + patron + r")\Z", mensaje))
                campo.max_length = longitud
                campo.widget.attrs.update(pattern=patron, title=mensaje, maxlength=longitud, inputmode=modo)
            elif isinstance(campo, forms.RegexField):
                # El usuario admite Unicode en Python; no copiar \w a JavaScript.
                if nombre == "username":
                    campo.validators.append(RegexValidator(r"\A[\w.]{4,30}\Z", "Usa de 4 a 30 letras, dígitos, puntos o guiones bajos."))
            if isinstance(campo, forms.CharField) and not isinstance(campo, forms.ChoiceField):
                campo.validators.append(RegexValidator(
                    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
                    "El texto contiene caracteres de control no permitidos.", inverse_match=True,
                ))
