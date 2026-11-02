from dataclasses import dataclass


@dataclass(frozen=True)
class PromocionOutputDTO:
    id: str
    nombre: str
    tipo: str
    estado: str
    producto_id: str | None
    descuento_valor: float
    vigencia_desde: str | None
    vigencia_hasta: str | None

    @classmethod
    def desde_entidad(cls, p) -> "PromocionOutputDTO":
        return cls(
            id=str(p.id),
            nombre=p.nombre,
            tipo=p.tipo.value,
            estado=p.estado.value,
            producto_id=p.producto_id,
            descuento_valor=float(p.descuento.valor) if p.descuento else 0.0,
            vigencia_desde=p.vigencia_desde.isoformat() if p.vigencia_desde else None,
            vigencia_hasta=p.vigencia_hasta.isoformat() if p.vigencia_hasta else None,
        )

