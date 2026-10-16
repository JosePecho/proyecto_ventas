from django.db import models


class VentaModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    numero_ticket = models.CharField(max_length=20, unique=True, db_index=True)
    cajero_id = models.UUIDField()
    turno_caja_id = models.UUIDField(null=True, blank=True, db_index=True)
    cliente_id = models.UUIDField(null=True, blank=True)
    estado = models.CharField(max_length=20, db_index=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    moneda = models.CharField(max_length=3, default="PEN")
    observacion = models.CharField(max_length=255, blank=True, default="")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_venta"
        ordering = ["-fecha_creacion"]

    def __str__(self) -> str:
        return f"Ticket {self.numero_ticket} - {self.total} {self.moneda}"

