from django.db import models


class MovimientoCajaModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    turno = models.ForeignKey("cash_register.TurnoCajaModel", on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=20)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    referencia = models.CharField(max_length=80, blank=True, default="")
    usuario_id = models.UUIDField(null=True, blank=True)
    observacion = models.CharField(max_length=255, blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cash_movimiento_caja"
        ordering = ["fecha_creacion"]

    def __str__(self) -> str:
        return f"{self.tipo} {self.monto}"

