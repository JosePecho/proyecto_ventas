from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.shared.infrastructure.logging.json_logger import get_logger

logger = get_logger("auditoria")


class RegistrarAuditoria:
    def __init__(self, repo: AuditoriaRepository):
        self._repo = repo

    def ejecutar(
        self,
        accion: str,
        entidad: str,
        entidad_id: str,
        usuario_id: str = "",
        detalle: dict | None = None,
        ip: str = "",
    ) -> str:
        registro = RegistroAuditoria.crear(accion, entidad, entidad_id, usuario_id, detalle, ip)
        self._repo.guardar(registro)
        logger.info(
            "Auditoria registrada",
            extra={
                "accion": accion,
                "entidad": f"{entidad}:{entidad_id}",
                "usuario": usuario_id,
            },
        )
        return str(registro.id)

