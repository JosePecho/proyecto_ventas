from django.db import models


class DetalleVentaModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    venta = models.ForeignKey("sales.VentaModel", on_delete=models.CASCADE, related_name="detalles")
    producto_id = models.UUIDField(db_index=True)
    producto_nombre = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    pct_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_detalle_venta"

    def __str__(self) -> str:
        return f"{self.producto_nombre} x{self.cantidad}"

