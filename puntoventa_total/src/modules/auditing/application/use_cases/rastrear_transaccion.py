"""Historial completo de una entidad (ej. una venta y todas sus acciones)."""
from src.modules.auditing.application.dto.auditoria_dto import AuditoriaDTO
from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.shared.application.exceptions.application_exception import NotFoundException


class RastrearTransaccion:
    def __init__(self, repo: AuditoriaRepository):
        self._repo = repo

    def ejecutar(self, entidad: str, entidad_id: str) -> dict:
        registros = self._repo.trazas_de_entidad(entidad, entidad_id)
        if not registros:
            raise NotFoundException(f"No hay trazas para {entidad}:{entidad_id}")
        return {
            "entidad": entidad,
            "entidad_id": entidad_id,
            "eventos": [AuditoriaDTO.desde_entidad(r) for r in registros],
            "cantidad": len(registros),
            "primera_accion": registros[-1].accion if registros else "",
            "ultima_accion": registros[0].accion if registros else "",
        }

