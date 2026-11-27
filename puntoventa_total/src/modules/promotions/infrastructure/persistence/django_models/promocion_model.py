from django.db import models


class PromocionModel(models.Model):
    componentes = models.JSONField(default=list, blank=True)
    id = models.UUIDField(primary_key=True, editable=False)
    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20)
    estado = models.CharField(max_length=20, db_index=True)
    producto_id = models.UUIDField(null=True, blank=True, db_index=True)
    categoria_id = models.UUIDField(null=True, blank=True)
    descuento_valor = models.DecimalField(max_digits=12, decimal_places=2)
    tope = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cantidad_requerida = models.PositiveSmallIntegerField(default=0)
    cantidad_gratuita = models.PositiveSmallIntegerField(default=0)
    vigencia_desde = models.DateTimeField(null=True, blank=True)
    vigencia_hasta = models.DateTimeField(null=True, blank=True)
    aplica_clientes_frecuentes = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "promotions_promocion"
        ordering = ["-vigencia_desde"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.tipo}/{self.estado})"

