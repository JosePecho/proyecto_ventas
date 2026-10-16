from abc import ABC, abstractmethod
from typing import Sequence


class ExportadorReportePort(ABC):
    @abstractmethod
    def exportar(self, encabezados: Sequence[str], filas: Sequence[Sequence], nombre: str) -> dict:
        """Devuelve {"contenido": bytes, "content_type": str, "nombre_archivo": str}."""
        ...

