"""Entidad Producto: identificable por codigo de barras y con precio compuesto."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from src.modules.catalog.domain.enums.estado_producto import EstadoProducto
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoDescontinuado
from src.modules.catalog.domain.value_objects.precio import Precio
from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.value_objects.codigo_barras import CodigoBarras
from src.shared.domain.value_objects.monto import Monto


@dataclass
class Producto(BaseEntity):
    nombre: str = ""
    descripcion: str = ""
    codigo_barras: CodigoBarras = None
    precio: Precio = None
    categoria_id: Optional[str] = None
    estado: EstadoProducto = EstadoProducto.ACTIVO
    imagen: str = ""
    unidad_medida: str = "UND"
    requiere_stock: bool = True
    stock_minimo: int = 5
    fecha_vencimiento: Optional[date] = None

    def __post_init__(self) -> None:
        self._requerir(self.nombre, "nombre", 150)
        if self.stock_minimo < 0:
            raise ValueError("El stock minimo no puede ser negativo")
        if self.codigo_barras is None or not isinstance(self.codigo_barras, CodigoBarras):
            self.codigo_barras = CodigoBarras(self.codigo_barras)
        if self.precio is None or not isinstance(self.precio, Precio):
            raise TypeError("Producto requiere un value object Precio")
        if not isinstance(self.estado, EstadoProducto):
            self.estado = EstadoProducto(self.estado)

    @property
    def precio_venta(self) -> Monto:
        return self.precio.venta

    @property
    def disponible_para_vender(self) -> bool:
        return self.activo and self.estado == EstadoProducto.ACTIVO

    def verificar_disponibilidad_venta(self) -> None:
        if not self.disponible_para_vender:
            raise ProductoDescontinuado(self.nombre)

    def actualizar_precios(self, costo: Monto, venta: Monto, margen_minimo: Decimal = Decimal("10")) -> None:
        self.precio = Precio(costo=costo, venta=venta, margen_minimo_pct=margen_minimo)
        self.marcar_actualizado()

    def descontinuar(self, motivo: str = "") -> None:
        self.estado = EstadoProducto.DESCONTINUADO
        self.activo = False
        self.marcar_actualizado()

    def reactivar(self) -> None:
        self.estado = EstadoProducto.ACTIVO
        self.activo = True
        self.marcar_actualizado()

    def renombrar(self, nombre: str) -> None:
        self._requerir(nombre, "nombre", 150)
        self.nombre = nombre
        self.marcar_actualizado()

