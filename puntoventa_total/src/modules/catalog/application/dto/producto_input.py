from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ProductoInputDTO:
    nombre: str
    descripcion: str
    codigo_barras: str
    costo: float
    precio_venta: float
    categoria_id: str | None = None
    imagen: str = ""
    unidad_medida: str = "UND"
    requiere_stock: bool = True
    stock_minimo: int = 5
    fecha_vencimiento: date | None = None


@dataclass(frozen=True)
class ActualizarProductoDTO:
    producto_id: str
    nombre: str | None = None
    descripcion: str | None = None
    costo: float | None = None
    precio_venta: float | None = None
    categoria_id: str | None = None
    stock_minimo: int | None = None
    fecha_vencimiento: date | None = None
    actualizar_vencimiento: bool = False
    codigo_barras: str | None = None

