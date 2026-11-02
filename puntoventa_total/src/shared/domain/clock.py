"""Reloj UTC sin dependencias de infraestructura."""
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
