"""Value object monetario con redondeo a 2 decimales y validacion de no negatividad."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from src.shared.domain.exceptions.validation_exception import ValidationException

DOS_DECIMALES = Decimal("0.01")


@dataclass(frozen=True)
class Monto:
    valor: Decimal
    moneda: str = "PEN"

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            object.__setattr__(self, "valor", Decimal(str(self.valor)))
        if self.valor < 0:
            raise ValidationException("El monto no puede ser negativo")
        if not self.moneda or len(self.moneda) != 3:
            raise ValidationException("Moneda invalida (debe ser ISO-4217, ej. PEN)")
        object.__setattr__(self, "valor", self.valor.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP))

    def __add__(self, otro: "Monto") -> "Monto":
        self._mismo_tipo(otro)
        return Monto(self.valor + otro.valor, self.moneda)

    def __sub__(self, otro: "Monto") -> "Monto":
        self._mismo_tipo(otro)
        resultado = self.valor - otro.valor
        if resultado < 0:
            raise ValidationException("El resultado del descuento excede el monto base")
        return Monto(resultado, self.moneda)

    def __mul__(self, escalar) -> "Monto":
        return Monto(Decimal(str(escalar)) * self.valor, self.moneda)

    def __rmul__(self, escalar) -> "Monto":
        return self.__mul__(escalar)

    def _mismo_tipo(self, otro: "Monto") -> None:
        if not isinstance(otro, Monto):
            raise ValidationException("Operacion invalida: se esperaba un Monto")
        if otro.moneda != self.moneda:
            raise ValidationException("No se pueden operar montos de distinta moneda")

    def es_cero(self) -> bool:
        return self.valor == 0

    def porcentaje(self, pct: Decimal) -> "Monto":
        if pct < 0 or pct > 100:
            raise ValidationException("El porcentaje debe estar entre 0 y 100")
        return Monto(self.valor * pct / Decimal("100"), self.moneda)

    def a_float(self) -> float:
        return float(self.valor)

    def __str__(self) -> str:
        return f"{self.valor} {self.moneda}"

