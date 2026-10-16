from dataclasses import dataclass


@dataclass(frozen=True)
class MovimientoDTO:
    id: str
    producto_id: str
    tipo: str
    cantidad: int
    stock_resultante: int
    referencia: str
    observacion: str
    fecha: str

    @classmethod
    def desde_entidad(cls, m) -> "MovimientoDTO":
        return cls(
            id=str(m.id),
            producto_id=m.producto_id,
            tipo=m.tipo.value,
            cantidad=m.cantidad,
            stock_resultante=m.stock_resultante,
            referencia=m.referencia,
            observacion=m.observacion,
            fecha=m.fecha.isoformat() if m.fecha else "",
        )

