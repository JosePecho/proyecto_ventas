import csv
import io
from typing import Sequence

from src.modules.reporting.application.ports.exportador_reporte_port import ExportadorReportePort


class CsvExporter(ExportadorReportePort):
    def exportar(self, encabezados: Sequence[str], filas: Sequence[Sequence], nombre: str) -> dict:
        buffer = io.StringIO()
        escritor = csv.writer(buffer)
        escritor.writerow(encabezados)
        escritor.writerows(filas)
        contenido = buffer.getvalue().encode("utf-8-sig")  # BOM para Excel
        return {
            "contenido": contenido,
            "content_type": "text/csv; charset=utf-8",
            "nombre_archivo": f"{nombre}.csv",
        }

