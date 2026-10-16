"""Agregado de existencia: stock consolidado por producto con reserva acotada."""
from __future__ import annotations

from dataclasses import dataclass

from src.modules.inventory.domain.exceptions.stock_exceptions import ExistenciaNegativa, StockException, StockInsuficiente
from src.shared.domain.entities.base_entity import BaseEntity


@dataclass
class Existencia(BaseEntity):
    producto_id: str = ""
    cantidad: int = 0
    reservada: int = 0

    def __post_init__(self) -> None:
        self._requerir(self.producto_id, "producto_id")
        if self.cantidad < 0 or self.reservada < 0:
            raise ExistenciaNegativa(self.producto_id)
        if self.reservada > self.cantidad:
            raise ExistenciaNegativa(self.producto_id)

    @property
    def disponible(self) -> int:
        """Stock fisico menos lo prometido (reservas vivas)."""
        return self.cantidad - self.reservada

    def aplicar_entrada(self, cantidad: int) -> None:
        self._validar_cantidad(cantidad)
        self.cantidad += cantidad
        self.marcar_actualizado()

    def aplicar_salida(self, cantidad: int) -> None:
        self._validar_cantidad(cantidad)
        if self.disponible < cantidad:
            raise StockInsuficiente(self.producto_id, self.disponible, cantidad)
        self.cantidad -= cantidad
        self.marcar_actualizado()

    def reservar(self, cantidad: int) -> None:
        self._validar_cantidad(cantidad)
        if self.disponible < cantidad:
            raise StockInsuficiente(self.producto_id, self.disponible, cantidad)
        self.reservada += cantidad
        self.marcar_actualizado()

    def liberar(self, cantidad: int) -> None:
        self._validar_cantidad(cantidad)
        self.reservada = max(0, self.reservada - cantidad)
        self.marcar_actualizado()

    def confirmar_reserva(self, cantidad: int) -> None:
        """Convierte reserva en salida fisica definitiva."""
        self._validar_cantidad(cantidad)
        if self.reservada < cantidad:
            raise StockInsuficiente(self.producto_id, self.reservada, cantidad)
        self.reservada -= cantidad
        self.cantidad -= cantidad
        self.marcar_actualizado()

    def _validar_cantidad(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise StockException(f"La cantidad debe ser positiva (recibido: {cantidad})")

    def con_stock_minimo(self, umbral: int) -> bool:
        return self.disponible <= umbral

