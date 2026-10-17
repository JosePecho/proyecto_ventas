from datetime import date
from typing import Optional, Sequence
from src.shared.infrastructure.database.date_bounds import date_bound

from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.auditing.infrastructure.persistence.mappers.auditoria_mapper import AuditoriaMapper


class DjangoAuditoriaRepository(AuditoriaRepository):
    def __init__(self):
        self._mapper = AuditoriaMapper()

    def guardar(self, registro: RegistroAuditoria) -> RegistroAuditoria:
        m = AuditoriaModel.objects.filter(pk=registro.id).first()
        AuditoriaMapper.a_modelo(registro, m).save()
        return registro

    def buscar_por_id(self, registro_id) -> Optional[RegistroAuditoria]:
        m = AuditoriaModel.objects.filter(pk=registro_id).first()
        return self._mapper.a_dominio(m) if m else None

    def consultar(self, accion=None, entidad=None, entidad_id=None, usuario_id=None, desde=None, hasta=None, limite=100):
        qs = AuditoriaModel.objects.all()
        if accion:
            qs = qs.filter(accion=accion)
        if entidad:
            qs = qs.filter(entidad=entidad)
        if entidad_id:
            qs = qs.filter(entidad_id=entidad_id)
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        if isinstance(desde, date):
            qs = qs.filter(fecha__gte=date_bound(desde))
        if isinstance(hasta, date):
            qs = qs.filter(fecha__lte=date_bound(hasta, end=True))
        return [self._mapper.a_dominio(m) for m in qs.order_by("-fecha")[:limite]]

    def trazas_de_entidad(self, entidad: str, entidad_id: str) -> Sequence[RegistroAuditoria]:
        qs = AuditoriaModel.objects.filter(entidad=entidad, entidad_id=entidad_id).order_by("-fecha")
        return [self._mapper.a_dominio(m) for m in qs]

