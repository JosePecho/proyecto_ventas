from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TurnoDTO:
    id: str
    cajero_id: str
    estado: str
    monto_apertura: float
    monto_cierre: Optional[float]
    monto_sistema: Optional[float]
    diferencia: Optional[float]
    fecha_apertura: str
    fecha_cierre: Optional[str]

    @classmethod
    def desde_entidad(cls, turno) -> "TurnoDTO":
        return cls(
            id=str(turno.id),
            cajero_id=turno.cajero_id,
            estado=turno.estado.value,
            monto_apertura=turno.monto_apertura.a_float(),
            monto_cierre=turno.monto_cierre.a_float() if turno.monto_cierre else None,
            monto_sistema=turno.monto_sistema.a_float() if turno.monto_sistema else None,
            diferencia=turno.diferencia.a_float() if turno.diferencia else None,
            fecha_apertura=turno.fecha_apertura.isoformat() if turno.fecha_apertura else "",
            fecha_cierre=turno.fecha_cierre.isoformat() if turno.fecha_cierre else None,
        )

