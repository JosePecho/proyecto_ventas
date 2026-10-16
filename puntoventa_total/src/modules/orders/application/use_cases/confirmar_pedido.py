"""Confirma el pedido y reserva stock para cada linea."""
from __future__ import annotations

from src.modules.orders.application.dto.pedido_output import PedidoOutputDTO
from src.modules.orders.application.ports.inventario_port import InventarioPort
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class ConfirmarPedido:
    def __init__(self, repo: PedidoRepository, inventario: InventarioPort, uow: UnitOfWork | None = None):
        self._repo = repo
        self._inventario = inventario
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, pedido_id: str) -> PedidoOutputDTO:
        with self._uow:
            agregado = self._repo.buscar_por_id(pedido_id)
            if agregado is None:
                from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoNoEncontrado

                raise PedidoNoEncontrado(pedido_id)

            referencia = agregado.reservar_referencia()
            # reserva stock primero: si algo falla, la transaccion lo revierte
            for l in agregado.lineas:
                self._inventario.reservar(l.producto_id, l.cantidad, referencia)
            agregado.confirmar()
            self._repo.guardar(agregado)

            return PedidoOutputDTO.desde_agregado(agregado)

