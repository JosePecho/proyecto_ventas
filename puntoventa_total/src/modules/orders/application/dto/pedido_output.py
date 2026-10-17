from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PedidoOutputDTO:
    id: str
    numero: str
    estado: str
    cliente_nombre: str
    total: float
    moneda: str
    hora_recojo: Optional[str]
    lineas: list[dict]

    @property
    def estado_label(self):
        return {"BORRADOR": "Carrito", "CONFIRMADO": "Pendiente",
                "EN_PREPARACION": "En preparación", "LISTO": "Listo",
                "ENTREGADO": "Entregado", "CANCELADO": "Cancelado"}[self.estado]

    @classmethod
    def desde_agregado(cls, agregado) -> "PedidoOutputDTO":
        p = agregado.pedido
        return cls(
            id=str(p.id),
            numero=p.numero,
            estado=p.estado.value,
            cliente_nombre=p.cliente_nombre,
            total=p.total,
            moneda=p.moneda,
            hora_recojo=p.hora_recojo.isoformat() if p.hora_recojo else None,
            lineas=agregado.resumen(),
        )

