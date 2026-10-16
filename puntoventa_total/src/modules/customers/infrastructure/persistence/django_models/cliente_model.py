from django.db import models


class ClienteModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    nombre = models.CharField(max_length=120, db_index=True)
    dni = models.CharField(max_length=8, unique=True, null=True, blank=True)
    email = models.EmailField(blank=True, default="")
    telefono = models.CharField(max_length=20, blank=True, default="")
    direccion = models.CharField(max_length=200, blank=True, default="")
    usuario_id = models.UUIDField(null=True, blank=True, db_index=True)
    puntos_fidelidad = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers_cliente"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.dni or 's/DNI'})"

