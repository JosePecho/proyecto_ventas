from datetime import date

from src.modules.auditing.application.dto.auditoria_dto import AuditoriaDTO, FiltroAuditoriaDTO
from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.shared.application.dto.pagination_dto import PageDTO


class ConsultarAuditoria:
    def __init__(self, repo: AuditoriaRepository):
        self._repo = repo

    def ejecutar(self, filtros: FiltroAuditoriaDTO, pagina: int = 1, por_pagina: int = 50) -> PageDTO[AuditoriaDTO]:
        registros = self._repo.consultar(
            accion=filtros.accion,
            entidad=filtros.entidad,
            entidad_id=filtros.entidad_id,
            usuario_id=filtros.usuario_id,
            desde=date.fromisoformat(filtros.desde) if filtros.desde else None,
            hasta=date.fromisoformat(filtros.hasta) if filtros.hasta else None,
            limite=filtros.limite,
        )
        inicio = (pagina - 1) * por_pagina
        fragmento = list(registros)[inicio : inicio + por_pagina]
        return PageDTO(
            items=[AuditoriaDTO.desde_entidad(r) for r in fragmento],
            total=len(list(registros)),
            pagina=pagina,
            por_pagina=por_pagina,
        )

