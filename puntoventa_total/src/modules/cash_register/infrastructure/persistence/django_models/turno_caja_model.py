from django.db import models


class TurnoCajaModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    cajero_id = models.UUIDField(db_index=True)
    estado = models.CharField(max_length=10, default="ABIERTO")
    monto_apertura = models.DecimalField(max_digits=12, decimal_places=2)
    monto_cierre = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monto_sistema = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_apertura = models.DateTimeField()
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    observaciones = models.CharField(max_length=255, blank=True, default="")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cash_turno_caja"
        ordering = ["-fecha_apertura"]

    def __str__(self) -> str:
        return f"Turno {self.id} ({self.estado})"

