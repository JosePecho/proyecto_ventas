"""Anulacion con devolucion de stock y evento correspondiente."""
from __future__ import annotations

from src.modules.sales.application.ports.auditoria_port import AuditoriaPort
from src.modules.sales.application.ports.inventario_port import InventarioPort
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class AnularVenta:
    def __init__(
        self,
        repo: VentaRepository,
        inventario: InventarioPort,
        auditoria: AuditoriaPort,
        uow: UnitOfWork | None = None,
    ):
        self._repo = repo
        self._inventario = inventario
        self._auditoria = auditoria
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, venta_id: str, motivo: str, usuario_id: str) -> dict:
        with self._uow:
            agregado = self._repo.buscar_por_id(venta_id)
            if agregado is None:
                from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

                raise VentaNoEncontrada(venta_id)

            pagada = agregado.venta.es_pagada
            referencia = f"ANULACION:{agregado.venta.numero_ticket}"
            agregado.anular(motivo, usuario_id)

            if pagada:
                for linea in agregado.lineas:
                    if linea.requiere_stock:
                        self._inventario.devolver(linea.producto_id, linea.cantidad, referencia, usuario_id)

            self._repo.guardar(agregado)
            self._auditoria.registrar(
                accion="VENTA_ANULADA",
                entidad="Venta",
                entidad_id=str(agregado.venta.id),
                usuario_id=usuario_id,
                detalle={"motivo": motivo, "total": agregado.venta.total},
            )
            return {"estado": agregado.venta.estado.value, "venta_id": str(agregado.venta.id)}

