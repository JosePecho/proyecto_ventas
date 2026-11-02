from dataclasses import dataclass


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
    accion: str | None = None
    entidad: str | None = None
    entidad_id: str | None = None
    usuario_id: str | None = None
    desde: str | None = None
    hasta: str | None = None
    limite: int | None = None

