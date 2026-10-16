from django.db import models


class MovimientoModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    producto_id = models.UUIDField(db_index=True)
    tipo = models.CharField(max_length=20)
    cantidad = models.PositiveIntegerField()
    stock_resultante = models.IntegerField()
    referencia = models.CharField(max_length=80, blank=True, default="")
    usuario_id = models.UUIDField(null=True, blank=True)
    lote_id = models.UUIDField(null=True, blank=True)
    observacion = models.CharField(max_length=255, blank=True, default="")
    fecha = models.DateTimeField(db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_movimiento"
        ordering = ["-fecha"]
        indexes = [models.Index(fields=["producto_id", "fecha"])]

    def __str__(self) -> str:
        return f"{self.tipo} {self.cantidad} -> {self.stock_resultante}"

