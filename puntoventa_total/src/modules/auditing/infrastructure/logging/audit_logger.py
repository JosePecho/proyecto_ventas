"""Logger dedicado: espejo en archivo para retencion de auditoria."""
from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings


class AuditLogger:
    NOMBRE = "puntoventa.auditoria"

    @classmethod
    def logger(cls) -> logging.Logger:
        logger = logging.getLogger(cls.NOMBRE)
        if not logger.handlers:
            Path(settings.BASE_DIR, "logs").mkdir(exist_ok=True)
            handler = logging.FileHandler(Path(settings.BASE_DIR, "logs", "auditoria.log"), encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        return logger

    @classmethod
    def registrar(cls, accion: str, entidad: str, entidad_id: str, usuario_id: str = "") -> None:
        cls.logger().info("%s | %s:%s | usuario=%s", accion, entidad, entidad_id, usuario_id)

