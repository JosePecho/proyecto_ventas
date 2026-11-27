from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from django.db import connection, transaction

from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel


class DjangoStockRepository(StockRepository):
    def __init__(self):
        self._bloqueadas: dict[str, ExistenciaModel] = {}
        self._umbrales: dict[str, int] = {}
        self._cache_transaction: tuple[object, ...] | None = None

    @contextmanager
    def cache_scope(self) -> Iterator[None]:
        if not connection.in_atomic_block:
            raise RuntimeError("cache_scope requiere una transacción activa")
        if self._cache_transaction is not None:
            raise RuntimeError("cache_scope ya está activo")
        self._cache_transaction = tuple(connection.atomic_blocks)
        try:
            yield
            self._cache_scope_is_active()
        finally:
            self._bloqueadas.clear()
            self._umbrales.clear()
            self._cache_transaction = None

    def _cache_scope_is_active(self) -> bool:
        if self._cache_transaction is None:
            return False
        if (
            not connection.in_atomic_block
            or tuple(connection.atomic_blocks) != self._cache_transaction
        ):
            self._bloqueadas.clear()
            self._umbrales.clear()
            raise RuntimeError("cache_scope no puede abarcar varias transacciones")
        return True

    def disponibles(self, producto_ids) -> dict[str, int]:
        ids = [str(pid) for pid in producto_ids]
        resultado = dict.fromkeys(ids, 0)
        for pid, cantidad, reservada in ExistenciaModel.objects.filter(producto_id__in=ids).values_list(
            "producto_id", "cantidad", "reservada"
        ):
            resultado[str(pid)] = cantidad - reservada
        return resultado

    def obtener(self, producto_id: str) -> Existencia | None:
        cache_scope_active = self._cache_scope_is_active()
        qs = ExistenciaModel.objects.filter(producto_id=producto_id)
        if connection.in_atomic_block:
            # Serializa tambien la primera recepcion, antes de crear la existencia.
            from src.modules.catalog.infrastructure.persistence.django_models.producto_model import (
                ProductoModel,
            )

            productos = ProductoModel.objects.select_for_update().filter(pk=producto_id)
            if cache_scope_active:
                producto = productos.only("stock_minimo").first()
                self._umbrales[str(producto_id)] = producto.stock_minimo if producto is not None else 5
            else:
                list(productos.values_list("pk", flat=True))
            qs = qs.select_for_update()
        m = qs.first()
        if m is None:
            return None
        if cache_scope_active:
            self._bloqueadas[str(m.pk)] = m
        return Existencia(
            id=m.id,
            producto_id=str(m.producto_id),
            cantidad=m.cantidad,
            reservada=m.reservada,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    def disponible(self, producto_id: str) -> int:
        m = ExistenciaModel.objects.filter(producto_id=producto_id).first()
        return (m.cantidad - m.reservada) if m else 0

    def guardar(self, existencia: Existencia) -> Existencia:
        cache_scope_active = self._cache_scope_is_active()
        m = None
        if cache_scope_active:
            m = self._bloqueadas.pop(str(existencia.id), None)
        if m is None:
            m = ExistenciaModel.objects.filter(id=existencia.id).first()
        anterior = m.cantidad - m.reservada if m else 0
        m = m or ExistenciaModel(id=existencia.id)
        m.producto_id = UUID(str(existencia.producto_id))
        m.cantidad = existencia.cantidad
        m.reservada = existencia.reservada
        m.activo = existencia.activo
        m.save()
        minimo = None
        if cache_scope_active:
            minimo = self._umbrales.pop(str(existencia.producto_id), None)
        if minimo is None:
            minimo = self.umbral_minimo(str(existencia.producto_id))
        if anterior >= minimo and existencia.disponible < minimo:
            producto_id, disponible = str(existencia.producto_id), existencia.disponible

            def notificar():
                from src.modules.inventory.infrastructure.factories import construir_notificador

                construir_notificador().notificar_stock_minimo(producto_id, disponible, minimo)

            transaction.on_commit(notificar, robust=True)
        return existencia

    def umbral_minimo(self, producto_id: str, defecto: int = 5) -> int:
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel

        valor = ProductoModel.objects.filter(pk=producto_id).values_list("stock_minimo", flat=True).first()
        return defecto if valor is None else valor

    def listar_existencias(self) -> list[dict]:
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel

        existencias = {str(e.producto_id): e for e in ExistenciaModel.objects.filter(activo=True)}
        filas = []
        for p in ProductoModel.objects.filter(activo=True, requiere_stock=True):
            e = existencias.get(str(p.id))
            cantidad, reservada = (e.cantidad, e.reservada) if e else (0, 0)
            filas.append(
                {
                    "producto_id": str(p.id), "producto_nombre": p.nombre,
                    "cantidad": cantidad, "reservada": reservada, "disponible": cantidad - reservada,
                    "stock_minimo": p.stock_minimo, "bajo_minimo": cantidad - reservada < p.stock_minimo,
                }
            )
        return filas

    def productos_bajo_minimo(self, umbral: int | None = None) -> list[dict]:
        return [
            f for f in self.listar_existencias()
            if f["disponible"] < (f["stock_minimo"] if umbral is None else umbral)
        ]

