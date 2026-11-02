"""Ilustraciones locales para productos que aun no tienen fotografia."""
from django import template
from django.templatetags.static import static
from django.utils.text import slugify

register = template.Library()


@register.simple_tag
def imagen_ilustrativa(nombre):
    nombre = slugify(nombre)
    tipos = (
        ("aceite", "aceite"), ("agua", "agua"), ("gaseosa", "gaseosa"),
        ("rehidratante", "agua"), ("jugo", "jugo"), ("yogur", "yogur"),
        ("evaporada", "conserva"), ("leche", "leche"), ("queso", "queso"),
        ("atun", "conserva"), ("fideos", "fideos"), ("galletas", "galletas"),
        ("chocolate", "chocolate"), ("papa", "snacks"), ("mani", "snacks"),
        ("papel", "papel"), ("pasta-dental", "pasta"), ("jabon", "jabon"),
        ("detergente", "limpieza"), ("lejia", "limpieza"), ("lavavajilla", "limpieza"),
    )
    tipo = next((tipo for palabra, tipo in tipos if palabra in nombre), "abarrotes")
    return static(f"images/productos/{tipo}.svg")
