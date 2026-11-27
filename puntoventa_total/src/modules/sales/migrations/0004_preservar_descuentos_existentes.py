from decimal import Decimal
from django.db import migrations
from django.db.models import Sum


def preservar(apps, schema_editor):
    Venta = apps.get_model("sales", "VentaModel")
    Detalle = apps.get_model("sales", "DetalleVentaModel")
    for venta in Venta.objects.filter(descuento__gt=0, subtotal__gt=0, descuento_venta_pct=0).iterator():
        lineas = Detalle.objects.filter(venta_id=venta.id).aggregate(total=Sum("descuento"))["total"] or Decimal(0)
        extra = max(Decimal(0), venta.descuento - lineas)
        porcentaje = min(Decimal(100), extra * 100 / venta.subtotal).quantize(Decimal("0.01"))
        Venta.objects.filter(pk=venta.pk).update(descuento_venta_pct=porcentaje)


class Migration(migrations.Migration):
    dependencies = [("sales", "0003_detalleventamodel_costo_unitario_and_more")]
    operations = [migrations.RunPython(preservar, migrations.RunPython.noop)]
