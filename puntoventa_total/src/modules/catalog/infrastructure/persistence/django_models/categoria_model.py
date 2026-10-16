from django.db import models


class CategoriaModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    descripcion = models.TextField(blank=True, default="")
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_categoria"
        ordering = ["orden", "nombre"]

    def __str__(self) -> str:
        return self.nombre

