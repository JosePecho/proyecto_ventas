"""Entrega: confirma la salida reservada del inventario."""
from __future__ import annotations

from src.modules.orders.application.dto.pedido_output import PedidoOutputDTO
from src.modules.orders.application.ports.inventario_port import InventarioPort
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class EntregarPedido:
    def __init__(self, repo: PedidoRepository, inventario: InventarioPort, uow: UnitOfWork | None = None):
        self._repo = repo
        self._inventario = inventario
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, pedido_id: str, usuario_id: str = "") -> PedidoOutputDTO:
        with self._uow:
            agregado = self._repo.buscar_por_id(pedido_id)
            if agregado is None:
                from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoNoEncontrado

                raise PedidoNoEncontrado(pedido_id)

            referencia = agregado.reservar_referencia()
            agregado.entregar()
            from src.modules.orders.infrastructure.factories import construir_reserva_repository

            reservas = construir_reserva_repository().listar_por_referencia(referencia)
            from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
            for linea in agregado.lineas:
                cantidad = sum(r.cantidad for r in reservas if r.producto_id == linea.producto_id and r.activa)
                if linea.requiere_stock and cantidad != linea.cantidad:
                    raise PedidoException("La reserva de stock no está completa; revise el inventario antes de entregar")
            for reserva in reservas:
                if reserva.activa:
                    self._inventario.confirmar_reserva(str(reserva.id), referencia, usuario_id)

            self._repo.guardar(agregado)
            return PedidoOutputDTO.desde_agregado(agregado)

