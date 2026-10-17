"""Limites de fechas en la zona de negocio configurada por Django."""
from datetime import date, datetime, time

from django.conf import settings
from django.utils import timezone


def date_bound(value: date | datetime, *, end: bool = False) -> datetime:
    result = value if isinstance(value, datetime) else datetime.combine(value, time.max if end else time.min)
    if settings.USE_TZ and timezone.is_naive(result):
        return timezone.make_aware(result, timezone.get_current_timezone())
    return result
