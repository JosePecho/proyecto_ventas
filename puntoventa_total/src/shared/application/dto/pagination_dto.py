"""DTO de paginacion reutilizable por todos los listados."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PageDTO(Generic[T]):
    items: Sequence[T]
    total: int
    pagina: int
    por_pagina: int

    @property
    def total_paginas(self) -> int:
        if self.total == 0:
            return 1
        return -(-self.total // self.por_pagina)

    @property
    def tiene_anterior(self) -> bool:
        return self.pagina > 1

    @property
    def tiene_siguiente(self) -> bool:
        return self.pagina < self.total_paginas

    def a_contexto(self) -> dict:
        return {
            "items": self.items,
            "total": self.total,
            "pagina": self.pagina,
            "por_pagina": self.por_pagina,
            "total_paginas": self.total_paginas,
            "tiene_anterior": self.tiene_anterior,
            "tiene_siguiente": self.tiene_siguiente,
        }

