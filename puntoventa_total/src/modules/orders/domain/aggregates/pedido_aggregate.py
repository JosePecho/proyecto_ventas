"""Agregado Pedido: lineas, total e invariantes de estado."""
from __future__ import annotations

from dataclasses import dataclass, field

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

    def agregar_producto(self, producto_id: str, nombre: str, cantidad: int, precio: Monto, requiere_stock: bool = True) -> DetallePedido:
        self._verificar_modificable()
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise PedidoException("La cantidad debe ser un entero mayor a cero")
        existente = next((elemento for elemento in self.lineas if elemento.producto_id == producto_id), None)
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
            requiere_stock=requiere_stock,
        )
        self.lineas.append(linea)
        self.recalcular_total()
        return linea

    def quitar_producto(self, producto_id: str) -> None:
        self._verificar_modificable()
        self.lineas = [linea for linea in self.lineas if linea.producto_id != str(producto_id)]
        self.recalcular_total()

    def _verificar_modificable(self) -> None:
        if self.pedido.estado != EstadoPedido.BORRADOR:
            raise PedidoException(f"El pedido en estado {self.pedido.estado.value} no admite cambios")

    def recalcular_total(self) -> float:
        self.pedido.total = float(sum((elemento.subtotal.valor for elemento in self.lineas), 0))
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
                "producto_id": elemento.producto_id,
                "nombre": elemento.producto_nombre,
                "cantidad": elemento.cantidad,
                "precio": elemento.precio_unitario.a_float(),
                "subtotal": elemento.subtotal.a_float(),
            }
            for elemento in self.lineas
        ]

