from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProductoInputDTO:
    nombre: str
    descripcion: str
    codigo_barras: str
    costo: float
    precio_venta: float
    categoria_id: Optional[str] = None
    imagen: str = ""
    unidad_medida: str = "UND"
    requiere_stock: bool = True


@dataclass(frozen=True)
class ActualizarProductoDTO:
    producto_id: str
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    costo: Optional[float] = None
    precio_venta: Optional[float] = None
    categoria_id: Optional[str] = None

