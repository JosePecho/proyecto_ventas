"""Agregado Pedido: lineas, total e invariantes de estado."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.modules.orders.domain.entities.detalle_pedido import DetallePedido
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.modules.orders.domain.events.pedido_cancelado import PedidoCancelado
from src.modules.orders.domain.events.pedido_confirmado import PedidoConfirmado
from src.modules.orders.domain.events.pedido_listo import PedidoListo
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.shared.domain.value_objects.monto import Monto


@dataclass
class PedidoAggregate:
    pedido: Pedido
    lineas: list[DetallePedido] = field(default_factory=list)

    def agregar_producto(self, producto_id: str, nombre: str, cantidad: int, precio: Monto) -> DetallePedido:
        self._verificar_modificable()
        existente = next((l for l in self.lineas if l.producto_id == producto_id), None)
        if existente:
            existente.cambiar_cantidad(existente.cantidad + cantidad)
            self.recalcular_total()
            return existente
        linea = DetallePedido(
            pedido_id=str(self.pedido.id),
            producto_id=producto_id,
            producto_nombre=nombre,
            cantidad=cantidad,
            precio_unitario=precio,
        )
        self.lineas.append(linea)
        self.recalcular_total()
        return linea

    def _verificar_modificable(self) -> None:
        if self.pedido.estado not in (EstadoPedido.BORRADOR, EstadoPedido.CONFIRMADO):
            raise PedidoException(f"El pedido en estado {self.pedido.estado.value} no admite cambios")

    def recalcular_total(self) -> float:
        self.pedido.total = float(sum((l.subtotal.valor for l in self.lineas), 0))
        return self.pedido.total

    def confirmar(self) -> None:
        if not self.lineas:
            raise PedidoException("No se puede confirmar un pedido vacio")
        self.pedido.transicionar_a(EstadoPedido.CONFIRMADO)
        self.pedido._publicar(PedidoConfirmado(pedido_id=str(self.pedido.id), total=self.pedido.total))

    def iniciar_preparacion(self) -> None:
        self.pedido.transicionar_a(EstadoPedido.EN_PREPARACION)

    def marcar_listo(self) -> None:
        self.pedido.transicionar_a(EstadoPedido.LISTO)
        self.pedido._publicar(PedidoListo(pedido_id=str(self.pedido.id), numero=self.pedido.numero))

    def entregar(self) -> None:
        self.pedido.transicionar_a(EstadoPedido.ENTREGADO)

    def cancelar(self, motivo: str = "", usuario_id: str = "") -> None:
        if not self.pedido.es_cancelable:
            raise PedidoException(f"No se puede cancelar un pedido {self.pedido.estado.value}")
        self.pedido.cancelar(motivo)
        self.pedido._publicar(
            PedidoCancelado(pedido_id=str(self.pedido.id), motivo=motivo, usuario_id=usuario_id)
        )

    def reservar_referencia(self) -> str:
        return f"PEDIDO:{self.pedido.numero}"

    def resumen(self) -> list[dict]:
        return [
            {
                "producto_id": l.producto_id,
                "nombre": l.producto_nombre,
                "cantidad": l.cantidad,
                "precio": l.precio_unitario.a_float(),
                "subtotal": l.subtotal.a_float(),
            }
            for l in self.lineas
        ]

