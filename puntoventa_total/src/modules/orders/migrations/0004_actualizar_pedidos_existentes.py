from django.db import migrations


def actualizar(apps, schema_editor):
    Pedido = apps.get_model("orders", "PedidoModel")
    Usuario = apps.get_model("identity", "UsuarioModel")
    Reserva = apps.get_model("inventory", "ReservaModel")
    Producto = apps.get_model("catalog", "ProductoModel")
    Detalle = apps.get_model("orders", "DetallePedidoModel")
    for pedido in Pedido.objects.exclude(cliente_id=None).iterator():
        email = Usuario.objects.filter(pk=pedido.cliente_id).values_list("email", flat=True).first()
        if email:
            Pedido.objects.filter(pk=pedido.pk, cliente_email="").update(cliente_email=email)
    for numero in Pedido.objects.filter(estado__in=["CONFIRMADO", "EN_PREPARACION", "LISTO"]).values_list("numero", flat=True).iterator():
        Reserva.objects.filter(referencia=f"PEDIDO:{numero}", confirmada=False, liberada=False).update(permanente=True)
    Detalle.objects.filter(producto_id__in=Producto.objects.filter(requiere_stock=False).values("id")).update(requiere_stock=False)


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0003_detallepedidomodel_requiere_stock"),
        ("inventory", "0002_reservamodel_permanente"),
        ("identity", "0001_initial"),
        ("catalog", "0003_categorias_catalogo_web"),
    ]
    operations = [migrations.RunPython(actualizar, migrations.RunPython.noop)]
