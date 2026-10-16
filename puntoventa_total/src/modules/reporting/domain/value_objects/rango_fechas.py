from dataclasses import dataclass
from datetime import date, timedelta

from src.shared.domain.exceptions.validation_exception import ValidationException


@dataclass(frozen=True)
class RangoFechas:
    desde: date
    hasta: date

    def __post_init__(self) -> None:
        if self.hasta < self.desde:
            raise ValidationException("La fecha fin no puede ser anterior a la de inicio")
        if (self.hasta - self.desde).days > 366:
            raise ValidationException("El rango no puede superar un anio")

    @classmethod
    def hoy(cls) -> "RangoFechas":
        return cls(desde=date.today(), hasta=date.today())

    @classmethod
    def ultimos_dias(cls, dias: int = 30) -> "RangoFechas":
        hoy = date.today()
        return cls(desde=hoy - timedelta(days=dias), hasta=hoy)

    @classmethod
    def del_mes(cls, referencia: date | None = None) -> "RangoFechas":
        referencia = referencia or date.today()
        primero = referencia.replace(day=1)
        ultimo = (primero + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return cls(desde=primero, hasta=ultimo)

    def en_dias(self) -> list[date]:
        return [self.desde + timedelta(days=i) for i in range((self.hasta - self.desde).days + 1)]

