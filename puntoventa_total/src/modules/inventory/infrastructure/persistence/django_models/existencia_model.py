from django.db import models


class ExistenciaModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    producto_id = models.UUIDField(unique=True, db_index=True)
    cantidad = models.IntegerField(default=0)
    reservada = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_existencia"

    def __str__(self) -> str:
        return f"Producto {self.producto_id}: {self.cantidad} (reservada {self.reservada})"

