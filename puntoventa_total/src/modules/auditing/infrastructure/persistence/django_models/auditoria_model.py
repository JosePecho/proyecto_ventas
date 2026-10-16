from django.db import models


class AuditoriaModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    accion = models.CharField(max_length=40, db_index=True)
    entidad = models.CharField(max_length=60, db_index=True)
    entidad_id = models.CharField(max_length=64, db_index=True)
    usuario_id = models.UUIDField(null=True, blank=True, db_index=True)
    detalle = models.JSONField(default=dict)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(db_index=True, auto_now_add=True)

    class Meta:
        db_table = "auditing_registro"
        ordering = ["-fecha"]
        indexes = [models.Index(fields=["entidad", "entidad_id", "fecha"])]

    def __str__(self) -> str:
        return f"{self.accion} {self.entidad}:{self.entidad_id}"

