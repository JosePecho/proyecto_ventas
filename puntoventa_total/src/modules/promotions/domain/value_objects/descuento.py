from dataclasses import dataclass
from decimal import Decimal

from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto


@dataclass(frozen=True)
class Descuento:
    valor: Decimal
    tipo: str
    tope: Decimal | None = None

    def __post_init__(self) -> None:
        if self.valor < 0:
            raise ValidationException("El descuento no puede ser negativo")

    @classmethod
    def porcentaje(cls, pct: Decimal, tope: Decimal | None = None) -> "Descuento":
        if pct <= 0 or pct > 100:
            raise ValidationException("El porcentaje debe estar entre 0 y 100")
        return cls(valor=pct, tipo="PORCENTAJE", tope=tope)

    @classmethod
    def monto_fijo(cls, monto: Monto) -> "Descuento":
        if monto.es_cero():
            raise ValidationException("El descuento fijo no puede ser cero")
        return cls(valor=monto.valor, tipo="MONTO_FIJO")

    def aplicar_a(self, monto_base: Monto) -> Monto:
        if self.tipo == "PORCENTAJE":
            resultado = monto_base.porcentaje(self.valor)
            if self.tope is not None:
                resultado = Monto(min(resultado.valor, self.tope), monto_base.moneda)
        else:
            resultado = Monto(min(self.valor, monto_base.valor), monto_base.moneda)
        return resultado

