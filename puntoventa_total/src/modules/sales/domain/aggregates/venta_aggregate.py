"""Agregado Venta: invariantes de carrito, totales y transiciones de estado."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Sequence

from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.sales.domain.entities.pago import Pago
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.events.venta_anulada import VentaAnulada
from src.modules.sales.domain.events.venta_pagada import VentaPagada
from src.modules.sales.domain.exceptions.venta_exceptions import (
    ProductoYaAgregado,
    VentaException,
)
from src.modules.sales.domain.services.calculadora_venta import CalculadoraVenta
from src.shared.domain.value_objects.monto import Monto


@dataclass
class VentaAggregate:
    venta: Venta
    lineas: list[DetalleVenta] = field(default_factory=list)
    pagos: list[Pago] = field(default_factory=list)
    descuento_venta_pct: Decimal = Decimal("0")

    def agregar_producto(self, producto_id: str, nombre: str, cantidad: int, precio: Monto) -> DetalleVenta:
        self.venta.verificar_modificable()
        existente = next((l for l in self.lineas if l.producto_id == producto_id), None)
        if existente:
            raise ProductoYaAgregado(nombre)
        linea = DetalleVenta(
            venta_id=str(self.venta.id),
            producto_id=producto_id,
            producto_nombre=nombre,
            cantidad=cantidad,
            precio_unitario=precio,
        )
        self.lineas.append(linea)
        return linea

    def modificar_cantidad(self, producto_id: str, nueva_cantidad: int) -> None:
        self.venta.verificar_modificable()
        linea = self._linea(producto_id)
        linea.cambiar_cantidad(nueva_cantidad)

    def eliminar_producto(self, producto_id: str) -> None:
        self.venta.verificar_modificable()
        self.lineas.remove(self._linea(producto_id))

    def aplicar_descuento_linea(self, producto_id: str, pct: Decimal) -> None:
        self.venta.verificar_modificable()
        self._linea(producto_id).aplicar_descuento_pct(pct)

    def aplicar_descuento_venta(self, pct: Decimal) -> None:
        self.venta.verificar_modificable()
        if pct < 0 or pct > 50:
            raise VentaException("El descuento de venta no puede superar el 50%")
        self.descuento_venta_pct = pct

    def _linea(self, producto_id: str) -> DetalleVenta:
        linea = next((l for l in self.lineas if l.producto_id == producto_id), None)
        if linea is None:
            raise VentaException(f"El producto {producto_id} no esta en la venta")
        return linea

    def calcular_totales(self) -> dict:
        subtotal = CalculadoraVenta.subtotal(self.lineas)
        descuentos = CalculadoraVenta.descuentos(self.lineas)
        extra = subtotal.porcentaje(self.descuento_venta_pct) if self.descuento_venta_pct else Monto(0, subtotal.moneda)
        total = subtotal - descuentos - extra
        self.venta.subtotal = subtotal.a_float()
        self.venta.descuento = (descuentos + extra).a_float()
        self.venta.total = total.a_float()
        self.venta.igv = CalculadoraVenta.desglose_igv(total)["igv"]
        return {
            "subtotal": self.venta.subtotal,
            "descuento": self.venta.descuento,
            "igv": self.venta.igv,
            "total": self.venta.total,
        }

    def registrar_pago(self, pago: Pago) -> None:
        if not self.lineas:
            raise VentaException("No se puede cobrar una venta sin productos")
        self.pagos.append(pago)

    def total_pagado(self) -> Decimal:
        return sum((p.monto.valor for p in self.pagos), Decimal("0"))

    def saldo_pendiente(self) -> Decimal:
        return Decimal(str(self.venta.total)) - self.total_pagado()

    def cerrar(self, usuario_id: str = "") -> None:
        """Confirmacion de negocio: solo cierra si esta pagado por completo."""
        self.calcular_totales()
        if self.total_pagado() < Decimal(str(self.venta.total)):
            from src.modules.sales.domain.exceptions.venta_exceptions import PagoInsuficiente

            raise PagoInsuficiente(float(Decimal(str(self.venta.total)) - self.total_pagado()))
        self.venta.marcar_pagada()
        self.venta._publicar(
            VentaPagada(
                venta_id=str(self.venta.id),
                total=self.venta.total,
                cajero_id=self.venta.cajero_id or usuario_id,
            )
        )

    def anular(self, motivo: str = "", usuario_id: str = "") -> None:
        if not self.venta.puede_anularse():
            self.venta.verificar_modificable()
        self.venta.anular(motivo)
        self.venta._publicar(
            VentaAnulada(
                venta_id=str(self.venta.id),
                total=self.venta.total,
                motivo=motivo,
                usuario_id=usuario_id,
            )
        )

    def requiere_devolucion_stock(self) -> bool:
        return self.venta.estado.value == "ANULADA" and bool(self.lineas)

    def resumen_lineas(self) -> Sequence[dict]:
        return [
            {
                "producto_id": l.producto_id,
                "nombre": l.producto_nombre,
                "cantidad": l.cantidad,
                "precio_unitario": l.precio_unitario.a_float(),
                "subtotal": l.subtotal.a_float(),
                "descuento": l.descuento.a_float(),
                "total": l.total.a_float(),
            }
            for l in self.lineas
        ]

