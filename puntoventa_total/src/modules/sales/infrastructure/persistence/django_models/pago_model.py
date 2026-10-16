from django.db import models


class PagoModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    venta = models.ForeignKey("sales.VentaModel", on_delete=models.CASCADE, related_name="pagos")
    metodo = models.CharField(max_length=20)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    vuelto = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    referencia = models.CharField(max_length=80, blank=True, default="")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_pago"

    def __str__(self) -> str:
        return f"{self.metodo} {self.monto}"

