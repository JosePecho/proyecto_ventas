from django.db import models


class LoteModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    producto_id = models.UUIDField(db_index=True)
    numero_lote = models.CharField(max_length=40)
    cantidad_inicial = models.PositiveIntegerField()
    cantidad_restante = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    proveedor = models.CharField(max_length=120, blank=True, default="")
    fecha_vencimiento = models.DateField(null=True, blank=True)
    fecha_recepcion = models.DateField()
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_lote"
        ordering = ["fecha_vencimiento", "fecha_recepcion"]
        indexes = [models.Index(fields=["producto_id", "fecha_vencimiento"])]

    def __str__(self) -> str:
        return f"Lote {self.numero_lote} ({self.cantidad_restante}/{self.cantidad_inicial})"

