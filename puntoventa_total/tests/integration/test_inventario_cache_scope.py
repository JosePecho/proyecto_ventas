from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext

from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.persistence.repositories.django_lote_repository import (
    DjangoLoteRepository,
)
from src.modules.inventory.infrastructure.persistence.repositories.django_stock_repository import (
    DjangoStockRepository,
)
from src.modules.sales.infrastructure.adapters import inventario_adapter as ventas_inventario

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True)]


def _inventario(cantidad=10, cantidad_lote=10, stock_minimo=5):
    producto = ProductoModel.objects.create(
        id=uuid4(),
        nombre="Producto cache inventario",
        codigo_barras=f"{uuid4().int % 10**13:013d}",
        costo=Decimal("5.00"),
        precio_venta=Decimal("10.00"),
        estado="ACTIVO",
        stock_minimo=stock_minimo,
    )
    existencia = ExistenciaModel.objects.create(
        id=uuid4(), producto_id=producto.id, cantidad=cantidad
    )
    lote = LoteModel.objects.create(
        id=uuid4(),
        producto_id=producto.id,
        numero_lote=f"L-{uuid4().hex[:8]}",
        cantidad_inicial=cantidad_lote,
        cantidad_restante=cantidad_lote,
        fecha_recepcion=date.today(),
    )
    return producto, existencia, lote


def _selects(consultas, tabla):
    return [
        consulta["sql"]
        for consulta in consultas
        if consulta["sql"].lstrip().upper().startswith("SELECT")
        and tabla in consulta["sql"]
    ]


@pytest.mark.parametrize("repository_factory", [DjangoStockRepository, DjangoLoteRepository])
def test_cache_scope_requiere_transaccion_activa(repository_factory):
    with pytest.raises(RuntimeError, match="transacción activa"):
        with repository_factory().cache_scope():
            pass


def test_cache_scope_limpia_caches_al_salir():
    producto, _, _ = _inventario()
    stock_repo = DjangoStockRepository()
    lote_repo = DjangoLoteRepository()

    with transaction.atomic():
        with stock_repo.cache_scope(), lote_repo.cache_scope():
            assert stock_repo.obtener(str(producto.id)) is not None
            assert lote_repo.listar_por_producto(str(producto.id))
            assert stock_repo._bloqueadas
            assert stock_repo._umbrales
            assert lote_repo._bloqueados

        assert stock_repo._bloqueadas == {}
        assert stock_repo._umbrales == {}
        assert lote_repo._bloqueados == {}


def test_descuento_limpia_caches_si_falla_despues_de_cargar_stock_y_lotes(monkeypatch):
    producto, existencia, lote = _inventario(cantidad=2, cantidad_lote=1)
    stock_repo = DjangoStockRepository()
    lote_repo = DjangoLoteRepository()
    monkeypatch.setattr(ventas_inventario, "construir_stock_repository", lambda: stock_repo)
    monkeypatch.setattr(ventas_inventario, "construir_lote_repository", lambda: lote_repo)

    def fallar_despues_de_leer(cls, lotes, cantidad):
        assert len(lotes) == 1
        raise RuntimeError("fallo de prueba tras cargar el inventario")

    monkeypatch.setattr(
        PoliticaStock, "planificar_salida_peps", classmethod(fallar_despues_de_leer)
    )

    with pytest.raises(RuntimeError, match="fallo de prueba"):
        ventas_inventario.InventarioAdapter().descontar(
            str(producto.id), 1, "QA:cache-error"
        )

    assert stock_repo._bloqueadas == {}
    assert stock_repo._umbrales == {}
    assert lote_repo._bloqueados == {}
    assert ExistenciaModel.objects.get(pk=existencia.pk).cantidad == 2
    assert LoteModel.objects.get(pk=lote.pk).cantidad_restante == 1


def test_reutilizar_repositorios_en_otra_transaccion_lee_instancias_nuevas():
    producto, existencia, lote = _inventario()
    stock_repo = DjangoStockRepository()
    lote_repo = DjangoLoteRepository()

    with transaction.atomic():
        with stock_repo.cache_scope(), lote_repo.cache_scope():
            primera_existencia = stock_repo.obtener(str(producto.id))
            primeros_lotes = lote_repo.listar_por_producto(str(producto.id))
            modelo_existencia_anterior = stock_repo._bloqueadas[str(existencia.pk)]
            modelo_lote_anterior = lote_repo._bloqueados[str(lote.pk)]
            assert primera_existencia.cantidad == 10
            assert len(primeros_lotes) == 1

    assert stock_repo._bloqueadas == {}
    assert stock_repo._umbrales == {}
    assert lote_repo._bloqueados == {}

    ExistenciaModel.objects.filter(pk=existencia.pk).update(cantidad=7)
    LoteModel.objects.filter(pk=lote.pk).update(cantidad_restante=7)

    with transaction.atomic():
        with stock_repo.cache_scope(), lote_repo.cache_scope():
            nueva_existencia = stock_repo.obtener(str(producto.id))
            nuevos_lotes = lote_repo.listar_por_producto(str(producto.id))
            assert nueva_existencia.cantidad == 7
            assert nuevos_lotes[0].cantidad_restante == 7
            assert stock_repo._bloqueadas[str(existencia.pk)] is not modelo_existencia_anterior
            assert lote_repo._bloqueados[str(lote.pk)] is not modelo_lote_anterior


def test_cache_scope_no_permite_reutilizar_objetos_en_otra_transaccion():
    producto, _, _ = _inventario()
    stock_repo = DjangoStockRepository()
    lote_repo = DjangoLoteRepository()
    transaccion = transaction.atomic()
    transaccion.__enter__()
    stock_scope = stock_repo.cache_scope()
    lote_scope = lote_repo.cache_scope()
    stock_scope.__enter__()
    lote_scope.__enter__()

    try:
        existencia = stock_repo.obtener(str(producto.id))
        lotes = lote_repo.listar_por_producto(str(producto.id))
        assert existencia is not None
        assert lotes
    finally:
        transaccion.__exit__(None, None, None)

    with transaction.atomic():
        with pytest.raises(RuntimeError, match="varias transacciones"):
            stock_repo.guardar(existencia)
        with pytest.raises(RuntimeError, match="varias transacciones"):
            lote_repo.guardar(lotes[0])

    with pytest.raises(RuntimeError, match="varias transacciones"):
        stock_scope.__exit__(None, None, None)
    with pytest.raises(RuntimeError, match="varias transacciones"):
        lote_scope.__exit__(None, None, None)
    assert stock_repo._bloqueadas == {}
    assert stock_repo._umbrales == {}
    assert lote_repo._bloqueados == {}


def test_guardar_sin_lectura_previa_conserva_consultas_de_respaldo():
    producto, existencia_modelo, lote_modelo = _inventario()
    existencia = Existencia(
        id=existencia_modelo.id,
        producto_id=str(producto.id),
        cantidad=8,
    )
    lote = Lote(
        id=lote_modelo.id,
        producto_id=str(producto.id),
        numero_lote=lote_modelo.numero_lote,
        cantidad_inicial=lote_modelo.cantidad_inicial,
        cantidad_restante=8,
        fecha_recepcion=lote_modelo.fecha_recepcion,
    )
    stock_repo = DjangoStockRepository()
    lote_repo = DjangoLoteRepository()

    with transaction.atomic():
        with stock_repo.cache_scope(), lote_repo.cache_scope():
            with CaptureQueriesContext(connection) as consultas:
                stock_repo.guardar(existencia)
                lote_repo.guardar(lote)

    assert _selects(consultas, "inventory_existencia")
    assert _selects(consultas, "inventory_lote")
    assert ExistenciaModel.objects.get(pk=existencia_modelo.pk).cantidad == 8
    assert LoteModel.objects.get(pk=lote_modelo.pk).cantidad_restante == 8


def test_reutilizar_selects_bloqueados_y_umbral_sin_lecturas_repetidas():
    producto, existencia_modelo, lote_modelo = _inventario()
    stock_repo = DjangoStockRepository()
    lote_repo = DjangoLoteRepository()

    with transaction.atomic():
        with stock_repo.cache_scope(), lote_repo.cache_scope():
            with CaptureQueriesContext(connection) as consultas:
                existencia = stock_repo.obtener(str(producto.id))
                lotes = lote_repo.listar_por_producto(str(producto.id))
                existencia.aplicar_salida(1)
                lotes[0].descontar(1)
                stock_repo.guardar(existencia)
                lote_repo.guardar(lotes[0])

    assert len(_selects(consultas, "catalog_producto")) == 1
    assert len(_selects(consultas, "inventory_existencia")) == 1
    assert len(_selects(consultas, "inventory_lote")) == 1
    sql_producto = _selects(consultas, "catalog_producto")[0]
    assert "stock_minimo" in sql_producto
    assert ExistenciaModel.objects.get(pk=existencia_modelo.pk).cantidad == 9
    assert LoteModel.objects.get(pk=lote_modelo.pk).cantidad_restante == 9


@pytest.mark.skipif(connection.vendor != "mysql", reason="Requiere SELECT FOR UPDATE de InnoDB")
def test_reutilizacion_no_elimina_bloqueos_for_update():
    producto, _, _ = _inventario()
    stock_repo = DjangoStockRepository()
    lote_repo = DjangoLoteRepository()

    with transaction.atomic():
        with stock_repo.cache_scope(), lote_repo.cache_scope():
            with CaptureQueriesContext(connection) as consultas:
                assert stock_repo.obtener(str(producto.id)) is not None
                assert lote_repo.listar_por_producto(str(producto.id))

    sql_producto = _selects(consultas, "catalog_producto")[0].upper()
    sql_existencia = _selects(consultas, "inventory_existencia")[0].upper()
    sql_lote = _selects(consultas, "inventory_lote")[0].upper()
    assert "FOR UPDATE" in sql_producto
    assert "FOR UPDATE" in sql_existencia
    assert "FOR UPDATE" in sql_lote
