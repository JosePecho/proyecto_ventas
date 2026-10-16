from django.db import models


class ProductoModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    nombre = models.CharField(max_length=150, db_index=True)
    descripcion = models.TextField(blank=True, default="")
    codigo_barras = models.CharField(max_length=14, unique=True, db_index=True)
    costo = models.DecimalField(max_digits=12, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    categoria = models.ForeignKey(
        "catalog.CategoriaModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
    )
    estado = models.CharField(max_length=20)
    imagen = models.ImageField(upload_to="products/", blank=True, null=True)
    unidad_medida = models.CharField(max_length=10, default="UND")
    requiere_stock = models.BooleanField(default=True)
    stock_minimo = models.PositiveIntegerField(default=5)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_producto"
        ordering = ["nombre"]
        indexes = [models.Index(fields=["nombre", "estado"])]

    def __str__(self) -> str:
        return f"{self.nombre} [{self.codigo_barras}]"

