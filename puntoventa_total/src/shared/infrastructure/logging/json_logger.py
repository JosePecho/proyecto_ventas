"""Logger estructurado en JSON para trazabilidad y auditoria."""
from __future__ import annotations

import json
import logging
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now().isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
            "modulo": getattr(record, "modulo", None),
            "usuario": getattr(record, "usuario", None),
            "transaccion": getattr(record, "transaccion", None),
        }
        if record.exc_info:
            payload["excepcion"] = self.formatException(record.exc_info)
        return json.dumps({k: v for k, v in payload.items() if v is not None}, ensure_ascii=False)


def get_logger(nombre: str) -> logging.Logger:
    logger = logging.getLogger(nombre)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

