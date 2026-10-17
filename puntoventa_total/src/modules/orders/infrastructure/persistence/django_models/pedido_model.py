from django.db import models


class PedidoModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    numero = models.CharField(max_length=20, unique=True, db_index=True)
    cliente_id = models.UUIDField(null=True, blank=True, db_index=True)
    cliente_nombre = models.CharField(max_length=120)
    cliente_dni = models.CharField(max_length=8, blank=True, default="")
    cliente_telefono = models.CharField(max_length=20, blank=True, default="")
    cliente_email = models.EmailField(blank=True, default="")
    notificado_listo = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, db_index=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    moneda = models.CharField(max_length=3, default="PEN")
    hora_recojo = models.DateTimeField(null=True, blank=True)
    observaciones = models.CharField(max_length=255, blank=True, default="")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders_pedido"
        ordering = ["-fecha_creacion"]

    def __str__(self) -> str:
        return f"Pedido {self.numero} ({self.estado})"

