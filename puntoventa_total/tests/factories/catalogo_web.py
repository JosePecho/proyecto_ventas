from datetime import date
from uuid import uuid4

from src.modules.catalog.models import CategoriaModel, ProductoModel
from src.modules.inventory.models import ExistenciaModel, LoteModel

CATEGORIAS = [("Abarrotes", "abarrotes"), ("Bebidas", "bebidas"), ("Snacks", "snacks"),
              ("Limpieza", "limpieza"), ("Cuidado personal", "cuidado-personal")]


def categoria(nombre="Bebidas", slug="bebidas"):
    return CategoriaModel.objects.get_or_create(slug=slug, defaults={"id": uuid4(), "nombre": nombre})[0]


def producto(nombre="Agua mineral", cantidad=5, reservada=0, **kwargs):
    datos = dict(id=uuid4(), nombre=nombre, descripcion="Botella de agua mineral", estado="ACTIVO",
                 codigo_barras=f"{uuid4().int % 10**13:013d}", costo=5, precio_venta=10,
                 categoria=categoria(), stock_minimo=0)
    datos.update(kwargs)
    p = ProductoModel.objects.create(**datos)
    if cantidad is not None:
        ExistenciaModel.objects.create(id=uuid4(), producto_id=p.id, cantidad=cantidad, reservada=reservada)
        if cantidad:
            LoteModel.objects.create(id=uuid4(), producto_id=p.id, numero_lote=uuid4().hex,
                                    cantidad_inicial=cantidad, cantidad_restante=cantidad, fecha_recepcion=date.today())
    return p
