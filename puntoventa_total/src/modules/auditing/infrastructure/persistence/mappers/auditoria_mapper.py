import json
import uuid

from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel


class AuditoriaMapper:
    @staticmethod
    def a_dominio(m: AuditoriaModel) -> RegistroAuditoria:
        detalle = m.detalle
        if isinstance(detalle, str):
            try:
                detalle = json.loads(detalle)
            except json.JSONDecodeError:
                detalle = {"crudo": detalle}
        return RegistroAuditoria(
            id=m.id,
            accion=m.accion,
            entidad=m.entidad,
            entidad_id=m.entidad_id,
            usuario_id=str(m.usuario_id) if m.usuario_id else "",
            detalle=detalle,
            ip=m.ip or "",
            fecha=m.fecha,
        )

    @staticmethod
    def a_modelo(e: RegistroAuditoria, m: AuditoriaModel | None = None) -> AuditoriaModel:
        m = m or AuditoriaModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.accion = e.accion
        m.entidad = e.entidad
        m.entidad_id = e.entidad_id
        m.usuario_id = uuid.UUID(str(e.usuario_id)) if e.usuario_id else None
        m.detalle = e.detalle
        m.ip = e.ip or None
        return m

