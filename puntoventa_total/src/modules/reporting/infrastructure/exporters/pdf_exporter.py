import io
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

from src.modules.reporting.application.ports.exportador_reporte_port import ExportadorReportePort


class PdfExporter(ExportadorReportePort):
    def exportar(self, encabezados: Sequence[str], filas: Sequence[Sequence], nombre: str) -> dict:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        estilos = getSampleStyleSheet()
        elementos = [Paragraph(nombre.replace("_", " ").title(), estilos["Title"]), Spacer(1, 4 * mm)]

        datos = [list(encabezados)] + [list(fila) for fila in filas]
        tabla = Table(datos, repeatRows=1)
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elementos.append(tabla)
        doc.build(elementos)
        return {
            "contenido": buffer.getvalue(),
            "content_type": "application/pdf",
            "nombre_archivo": f"{nombre}.pdf",
        }

