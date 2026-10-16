"""Adaptador InventarioPort -> modulo inventory (capa anticorrupcion)."""
from __future__ import annotations

from typing import Iterable

from django.db import transaction

from src.modules.inventory.application.use_cases.confirmar_salida_reservada import ConfirmarSalidaReservada
from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
from src.modules.inventory.application.use_cases.descontar_stock import DescontarStock
from src.modules.inventory.application.use_cases.reservar_stock import ReservarStock
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.infrastructure.factories import (
    construir_lote_repository,
    construir_movimiento_repository,
    construir_reserva_repository,
    construir_stock_repository,
)
from src.modules.sales.application.ports.inventario_port import InventarioPort


class InventarioAdapter(InventarioPort):
    def descontar(self, producto_id: str, cantidad: int, referencia: str, usuario_id: str = "") -> int:
        return DescontarStock(
            construir_stock_repository(),
            construir_lote_repository(),
            construir_movimiento_repository(),
            uow=transaction.atomic(),
        ).ejecutar(producto_id, cantidad, referencia, usuario_id)

    def reservar(self, producto_id: str, cantidad: int, referencia: str) -> str:
        return ReservarStock(
            construir_stock_repository(), construir_reserva_repository(), uow=transaction.atomic()
        ).ejecutar(
            producto_id, cantidad, referencia
        )

    def confirmar_reserva(self, reserva_id: str, referencia: str, usuario_id: str = "") -> int:
        return ConfirmarSalidaReservada(
            construir_stock_repository(),
            construir_reserva_repository(),
            construir_movimiento_repository(),
            uow=transaction.atomic(),
            lote_repo=construir_lote_repository(),
        ).ejecutar(reserva_id, referencia, usuario_id)

    @transaction.atomic
    def devolver(self, producto_id: str, cantidad: int, referencia: str, usuario_id: str = "") -> int:
        """Devolucion por anulacion: entrada de stock compensatoria."""
        mov_repo: MovimientoRepository = construir_movimiento_repository()
        existencia = construir_stock_repository().obtener(producto_id)
        from src.modules.inventory.domain.entities.existencia import Existencia
        from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock

        existencia = existencia or Existencia(producto_id=producto_id)
        existencia.aplicar_entrada(cantidad)
        # Repone los lotes consumidos por la venta, conservando su vencimiento.
        lotes_repo = construir_lote_repository()
        referencia_venta = referencia.replace("ANULACION:", "VENTA:", 1)
        pendiente = cantidad
        for salida in mov_repo.kardex(producto_id, limite=None):
            if salida.tipo != TipoMovimiento.SALIDA_VENTA or salida.referencia != referencia_venta or not salida.lote_id:
                continue
            lote = lotes_repo.buscar_por_id(salida.lote_id)
            if lote is None:
                continue
            tomar = min(pendiente, salida.cantidad, lote.cantidad_inicial - lote.cantidad_restante)
            lote.cantidad_restante += tomar
            lotes_repo.guardar(lote)
            pendiente -= tomar
            if not pendiente:
                break
        if pendiente:
            # Compatibilidad con ventas historicas sin trazabilidad por lote.
            from src.modules.inventory.domain.entities.lote import Lote
            from uuid import uuid4
            lotes_repo.guardar(Lote(producto_id=producto_id, numero_lote=f"DEV-{uuid4().hex[:12]}",
                                   cantidad_inicial=pendiente, cantidad_restante=pendiente))
        construir_stock_repository().guardar(existencia)
        mov_repo.guardar(
            MovimientoStock(
                producto_id=producto_id,
                tipo=TipoMovimiento.DEVOLUCION,
                cantidad=cantidad,
                stock_resultante=existencia.cantidad,
                referencia=referencia,
                usuario_id=usuario_id,
            )
        )
        return existencia.cantidad

    def stock_disponible(self, producto_id: str) -> int:
        return ConsultarStock(construir_stock_repository()).ejecutar(producto_id).disponible

    def verificar_disponibilidad_lote(self, productos: Iterable[dict]) -> dict[str, int]:
        resultado = {}
        stock_repo = construir_stock_repository()
        for item in productos:
            disponible = stock_repo.disponible(str(item["producto_id"]))
            if disponible < item.get("cantidad", 1):
                from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente

                raise StockInsuficiente(item["producto_id"], disponible, item.get("cantidad", 1))
            resultado[str(item["producto_id"])] = disponible
        return resultado

