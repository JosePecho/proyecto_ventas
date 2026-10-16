from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.modules.auditing.infrastructure.persistence.repositories.django_auditoria_repository import (
    DjangoAuditoriaRepository,
)


def construir_auditoria_repository() -> AuditoriaRepository:
    return DjangoAuditoriaRepository()

