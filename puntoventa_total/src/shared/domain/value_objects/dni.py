"""Value object DNI peruano: 8 digitos exactos."""
from __future__ import annotations

import re
from dataclasses import dataclass

from src.shared.domain.exceptions.validation_exception import ValidationException

PATRON_DNI = re.compile(r"^\d{8}$")


@dataclass(frozen=True)
class DNI:
    valor: str

    def __post_init__(self) -> None:
        valor = str(self.valor).strip()
        if not PATRON_DNI.match(valor):
            raise ValidationException("El DNI debe contener exactamente 8 digitos")
        object.__setattr__(self, "valor", valor)

    def __str__(self) -> str:
        return self.valor

    def enmascarado(self) -> str:
        return f"{self.valor[:3]}****{self.valor[-1]}"

