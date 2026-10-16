from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class ProductoOutputDTO:
    id: str
    nombre: str
    descripcion: str
    codigo_barras: str
    costo: float
    precio_venta: float
    margen_pct: float
    categoria: Optional[str]
    estado: str
    imagen: str
    stock_disponible: Optional[int] = None
    stock_minimo: int = 5
    fecha_vencimiento: Optional[date] = None

    @classmethod
    def desde_entidad(cls, producto, categoria_nombre: str | None = None, stock: int | None = None):
        return cls(
            id=str(producto.id),
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            codigo_barras=str(producto.codigo_barras),
            costo=producto.precio.costo.a_float(),
            precio_venta=producto.precio.venta.a_float(),
            margen_pct=float(producto.precio.margen_pct()),
            categoria=categoria_nombre,
            estado=producto.estado.value,
            imagen=producto.imagen,
            stock_disponible=stock,
            stock_minimo=producto.stock_minimo,
            fecha_vencimiento=producto.fecha_vencimiento,
        )

