from django.db import models


class DetallePedidoModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    pedido = models.ForeignKey("orders.PedidoModel", on_delete=models.CASCADE, related_name="detalles")
    producto_id = models.UUIDField(db_index=True)
    producto_nombre = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders_detalle_pedido"

    def __str__(self) -> str:
        return f"{self.producto_nombre} x{self.cantidad}"

