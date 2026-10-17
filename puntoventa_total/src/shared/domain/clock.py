"""Reloj UTC sin dependencias de infraestructura."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
