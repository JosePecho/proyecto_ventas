from src.modules.sales.application.ports.auditoria_port import AuditoriaPort


class AuditoriaAdapter(AuditoriaPort):
    """Delega el registro al modulo de auditoria."""

    def registrar(self, accion: str, entidad: str, entidad_id: str, usuario_id: str, detalle: dict | None = None) -> None:
        from src.modules.auditing.application.use_cases.registrar_auditoria import RegistrarAuditoria
        from src.modules.auditing.infrastructure.factories import construir_auditoria_repository

        RegistrarAuditoria(construir_auditoria_repository()).ejecutar(
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            usuario_id=usuario_id,
            detalle=detalle or {},
        )

