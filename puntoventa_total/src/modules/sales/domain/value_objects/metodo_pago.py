from dataclasses import dataclass

from src.shared.domain.value_objects.monto import Monto


@dataclass(frozen=True)
class MetodoPago:
    tipo: str
    monto: Monto
    referencia: str = ""

    TIPOS = ("EFECTIVO", "TARJETA", "YAPE", "PLIN", "TRANSFERENCIA")

    def __post_init__(self) -> None:
        if self.tipo not in self.TIPOS:
            raise ValidationException(f"Metodo de pago invalido: {self.tipo}")
        if self.monto.es_cero():
            raise ValidationException("El monto del pago debe ser mayor a cero")

    @property
    def es_efectivo(self) -> bool:
        return self.tipo == "EFECTIVO"

from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

