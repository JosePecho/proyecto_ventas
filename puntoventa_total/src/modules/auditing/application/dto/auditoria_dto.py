from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AuditoriaDTO:
    id: str
    accion: str
    entidad: str
    entidad_id: str
    usuario_id: str
    detalle: dict
    ip: str
    fecha: str

    @classmethod
    def desde_entidad(cls, r) -> "AuditoriaDTO":
        return cls(
            id=str(r.id),
            accion=r.accion,
            entidad=r.entidad,
            entidad_id=r.entidad_id,
            usuario_id=r.usuario_id,
            detalle=r.detalle,
            ip=r.ip,
            fecha=r.fecha.isoformat(),
        )


@dataclass(frozen=True)
class FiltroAuditoriaDTO:
    accion: Optional[str] = None
    entidad: Optional[str] = None
    entidad_id: Optional[str] = None
    usuario_id: Optional[str] = None
    desde: Optional[str] = None
    hasta: Optional[str] = None
    limite: Optional[int] = None

