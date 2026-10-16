"""Value object para codigos de barras EAN-13 / interno."""
from __future__ import annotations

import re
from dataclasses import dataclass

from src.shared.domain.exceptions.validation_exception import ValidationException

PATRON = re.compile(r"^\d{8}$|^\d{12,14}$")


@dataclass(frozen=True)
class CodigoBarras:
    valor: str

    def __post_init__(self) -> None:
        valor = str(self.valor).strip().upper()
        if not PATRON.match(valor):
            raise ValidationException("Codigo de barras invalido (8 o 12-14 digitos)")
        object.__setattr__(self, "valor", valor)

    def checksum_ean13_valido(self) -> bool:
        """Valida el digito verificador segun el algoritmo EAN-13."""
        if len(self.valor) != 13:
            return False
        digitos = [int(d) for d in self.valor]
        suma = sum(d * (3 if i % 2 else 1) for i, d in enumerate(digitos[:12]))
        return (10 - suma % 10) % 10 == digitos[12]

    def __str__(self) -> str:
        return self.valor

