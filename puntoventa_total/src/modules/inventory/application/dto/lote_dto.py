from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class RecepcionLoteDTO:
    producto_id: str
    numero_lote: str
    cantidad: int
    costo_unitario: float
    proveedor: str = ""
    fecha_vencimiento: date | str | None = None


@dataclass(frozen=True)
class LoteDTO:
    id: str
    producto_id: str
    numero_lote: str
    cantidad_restante: int
    costo_unitario: Optional[float]
    proveedor: str
    fecha_vencimiento: Optional[str]
    vencido: bool

    @classmethod
    def desde_entidad(cls, lote) -> "LoteDTO":
        return cls(
            id=str(lote.id),
            producto_id=lote.producto_id,
            numero_lote=lote.numero_lote,
            cantidad_restante=lote.cantidad_restante,
            costo_unitario=lote.costo_unitario.a_float() if lote.costo_unitario else None,
            proveedor=lote.proveedor,
            fecha_vencimiento=lote.fecha_vencimiento.isoformat() if lote.fecha_vencimiento else None,
            vencido=lote.vencido(),
        )

