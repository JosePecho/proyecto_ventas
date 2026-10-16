from django.db import models


class ReservaModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    producto_id = models.UUIDField(db_index=True)
    cantidad = models.PositiveIntegerField()
    referencia = models.CharField(max_length=80, db_index=True)
    expira_en = models.DateTimeField()
    confirmada = models.BooleanField(default=False)
    liberada = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_reserva"
        indexes = [models.Index(fields=["confirmada", "liberada", "expira_en"])]

    def __str__(self) -> str:
        return f"Reserva {self.referencia}: {self.cantidad} u."

