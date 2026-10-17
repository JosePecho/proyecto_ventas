"""Categorias iniciales RF-026; conserva las categorias existentes."""
from uuid import NAMESPACE_URL, uuid5

from django.db import migrations
from django.db.models import Q


def crear_categorias(apps, schema_editor):
    categoria = apps.get_model("catalog", "CategoriaModel")
    for orden, (nombre, slug) in enumerate((
        ("Abarrotes", "abarrotes"), ("Bebidas", "bebidas"), ("Snacks", "snacks"),
        ("Limpieza", "limpieza"), ("Cuidado personal", "cuidado-personal"),
    )):
        if not categoria.objects.using(schema_editor.connection.alias).filter(Q(nombre=nombre) | Q(slug=slug)).exists():
            categoria.objects.using(schema_editor.connection.alias).create(
                id=uuid5(NAMESPACE_URL, f"catalogo/{slug}"), nombre=nombre, slug=slug, orden=orden,
            )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_productomodel_fecha_vencimiento_and_more")]
    operations = [migrations.RunPython(crear_categorias, migrations.RunPython.noop)]
