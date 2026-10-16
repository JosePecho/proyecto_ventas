from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PromocionInputDTO:
    nombre: str
    tipo: str
    descuento_valor: float
    producto_id: Optional[str] = None
    categoria_id: Optional[str] = None
    cantidad_requerida: int = 0
    cantidad_gratuita: int = 0
    vigencia_desde: Optional[str] = None
    vigencia_hasta: Optional[str] = None
    aplica_clientes_frecuentes: bool = False

