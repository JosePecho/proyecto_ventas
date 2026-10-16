from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VentaOutputDTO:
    id: str
    numero_ticket: str
    estado: str
    subtotal: float
    descuento: float
    igv: float
    total: float
    moneda: str
    cajero_id: str
    lineas: list[dict]
    total_pagado: float = 0.0

    @classmethod
    def desde_agregado(cls, agregado) -> "VentaOutputDTO":
        v = agregado.venta
        return cls(
            id=str(v.id),
            numero_ticket=v.numero_ticket,
            estado=v.estado.value,
            subtotal=v.subtotal,
            descuento=v.descuento,
            igv=v.igv,
            total=v.total,
            moneda=v.moneda,
            cajero_id=v.cajero_id,
            lineas=agregado.resumen_lineas(),
            total_pagado=float(agregado.total_pagado()),
        )

